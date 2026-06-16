from __future__ import annotations
import shutil

from rich.console import Console

from crewai_remotion.config import get_settings
from crewai_remotion.errors import ProductionError
from crewai_remotion.crews import (
    run_asset_research_crew,
    run_clearance_crew,
    run_creative_review_crew,
    run_development_crew,
    run_postproduction_crew,
    run_qc_crew,
    run_voice_director,
    run_visual_development,
    run_writers_room,
)
from crewai_remotion.gates.av_script import gate_av_script
from crewai_remotion.gates.clearance import gate_clearance
from crewai_remotion.gates.composed_frames import gate_composed_frames
from crewai_remotion.gates.coordinator import log_note, write_call_sheet
from crewai_remotion.gates.creative_brief import gate_creative_brief
from crewai_remotion.gates.hook_selection import gate_hook_selection
from crewai_remotion.gates.picture_lock import gate_picture_lock
from crewai_remotion.gates.qc_router import gate_qc
from crewai_remotion.gates.storyboard import gate_storyboard
from crewai_remotion.models.production_state import ProductionState, QCVerdict
from crewai_remotion.models.writers_room import ContinuityBible
from crewai_remotion.pipeline.topic import run_topic_pipeline
from crewai_remotion.tools.image_assets import build_queries_from_script, resolve_scene_images
from crewai_remotion.tools.music import attach_music
from crewai_remotion.tools.render_remotion import render_video
from crewai_remotion.tools.sfx import wire_sfx_to_spec
from crewai_remotion.tools.storyboard import render_storyboard
from crewai_remotion.tools.transcribe import transcribe_audio
from crewai_remotion.tools.tts import generate_voiceover
from crewai_remotion.delivery.package import package_delivery
from crewai_remotion.loops.evaluators import run_deterministic_evals
from crewai_remotion.loops.qa_vision import run_visual_qa
from crewai_remotion.tools.smoke_stills import smoke_test_stills
from crewai_remotion.tools.dailies import run_dailies
from crewai_remotion.loops.trace import TraceRecorder
from crewai_remotion.loops.flywheel import save_lessons_from_state

console = Console()


def _apply_scene_images(state: ProductionState) -> None:
    if not state.composed_frames or not state.scene_images:
        return
    for frame in state.composed_frames.frames:
        asset = state.scene_images.for_beat(frame.beat_id)
        if asset:
            frame.image_path = asset.public_path

_SCENE_TYPE_MAP: dict[str, str] = {
    "hook": "HookBeat",
    "point": "PointBeat",
    "stat": "StatBeat",
    "quote": "QuoteBeat",
    "cta": "CTABeat",
    "rehook": "HookBeat",
}

_BG_VARIANT_MAP: dict[str, str] = {
    "radial": "secondary",
    "gradient_mesh": "secondary",
    "solid": "primary",
    "gradient": "surface",
}

_MOTION_INTENT_MAP: dict[str, str] = {
    "enter_up": "enter_up",
    "fade_in": "fade_in",
    "scale_burst": "scale_burst",
    "slide_in": "slide_in",
}



def _normalize_scene_types(state: ProductionState) -> None:
    """Ensure scene fields match Remotion's Zod schema enums."""
    if not state.video_spec:
        return
    for scene in state.video_spec.scenes:
        scene.type = _SCENE_TYPE_MAP.get(scene.type, scene.type)
        bg = scene.background_variant
        if bg not in ("primary", "secondary", "surface"):
            scene.background_variant = _BG_VARIANT_MAP.get(bg, "secondary")
        mi = scene.motion_intent
        if mi not in ("enter_up", "fade_in", "scale_burst", "slide_in"):
            scene.motion_intent = _MOTION_INTENT_MAP.get(mi, "enter_up")


def _wire_audio_to_spec(state: ProductionState, captions: list | None = None) -> None:
    """Wire voiceover, music, and captions into the video spec after it exists."""
    if not state.video_spec:
        return
    settings = get_settings()
    out = state.run_output()
    remotion_public = settings.root / "remotion" / "public" / "runs" / state.run_id
    remotion_public.mkdir(parents=True, exist_ok=True)

    # Copy voiceover to public/ for Remotion access
    vo_src = out / "voice.wav"
    if vo_src.exists():
        shutil.copy2(vo_src, remotion_public / "voice.wav")
        state.video_spec.audio.voiceover = f"runs/{state.run_id}/voice.wav"

    # Copy music to public/ for Remotion access
    music_src = out / "music.mp3"
    if music_src.exists():
        shutil.copy2(music_src, remotion_public / "music.mp3")
        state.video_spec.audio.music_path = f"runs/{state.run_id}/music.mp3"
    else:
        # Clear any placeholder the Mograph TD may have set
        state.video_spec.audio.music_path = ""

    # Wire music metadata
    if state.brand:
        state.video_spec.audio.music_mood = state.brand.audio.music_mood
        state.video_spec.audio.music_volume = state.brand.audio.music_volume

    # Wire audio duration and captions (must be positive for Zod schema)
    dur = state.audio_duration_sec or state.duration_sec or 30.0
    state.video_spec.audio.duration_sec = max(dur, 1.0)
    if captions:
        state.video_spec.captions = captions


def _fail(message: str, state: ProductionState, phase: str, hint: str = "") -> None:
    raise ProductionError(
        message,
        phase=phase,
        hint=hint,
        run_dir=str(state.run_output()),
    )


def _save_artifacts(state: ProductionState) -> None:
    """Write production artifacts to disk."""
    import json
    out = state.run_output()
    if state.video_spec:
        (out / "video_spec.json").write_text(
            json.dumps(state.video_spec.to_remotion_props(), indent=2),
            encoding="utf-8",
        )
    if state.av_script:
        (out / "av_script.json").write_text(
            state.av_script.model_dump_json(indent=2), encoding="utf-8"
        )
    if state.creative_brief:
        (out / "creative_brief.json").write_text(
            state.creative_brief.model_dump_json(indent=2), encoding="utf-8"
        )
    if state.composed_frames:
        (out / "composed_frames.json").write_text(
            state.composed_frames.model_dump_json(indent=2), encoding="utf-8"
        )


def _run_audio_phase(state: ProductionState, recorder: TraceRecorder) -> list:
    """Run audio phase. Returns captions list."""
    with recorder.span("audio"):
        vo_path, tts_ok = generate_voiceover(state)
        if not tts_ok:
            log_note(state, "audio", "TTS failed — silent voiceover fallback used", ok=False)
        captions = transcribe_audio(vo_path, state)
        state.audio_duration_sec = _get_audio_duration(vo_path)
        state.voiceover_path = str(vo_path)
        attach_music(state)
        log_note(state, "audio", "TTS + captions ready")
    return captions


def _run_from_visual_dev(state: ProductionState, recorder: TraceRecorder) -> list:
    """Run visual development through audio. Returns captions list."""
    # ── Phase 2b: Visual Development ──
    with recorder.span("visual_development"):
        try:
            manifest_json = state.scene_images.model_dump_json() if state.scene_images else ""
            vd_result = run_visual_development(
                state.brand, state.av_script, manifest_json
            )
            state.mood_board = vd_result["mood_board"]
            state.style_bible = vd_result["style_bible"]
            state.style_frame_specs = vd_result["style_frame_specs"]
            state.environment_plan = vd_result["environment_plan"]
            state.type_spec = vd_result["type_spec"]
            state.illustration_plan = vd_result["illustration_plan"]
            state.rough_storyboard = vd_result["rough_storyboard"]
            state.composed_frames = vd_result["composed_frames"]
            _apply_scene_images(state)
        except Exception as exc:
            _fail(f"Visual development failed: {exc}", state, "visual_development")

    # ── Creative Review (table read for visuals) ──
    with recorder.span("creative_review"):
        try:
            review = run_creative_review_crew(
                state.composed_frames,
                state.creative_brief,
                state.brand,
            )
            state.creative_review_notes = review["creative_review"]
            state.art_review_notes = review["art_review"]
            state.layout_review_notes = review["layout_review"]
        except Exception as exc:
            log_note(state, "creative_review", f"Review skipped: {exc}", ok=False)

    # ── Clearance (Pipeline TD + Brand Guardian) ──
    with recorder.span("clearance"):
        try:
            clearance = run_clearance_crew(
                state.composed_frames,
                state.style_bible,
                state.brand,
                state.av_script,
            )
            state.feasibility_report = clearance["feasibility"]
            state.brand_compliance = clearance["brand_compliance"]
        except Exception as exc:
            log_note(state, "clearance", f"Clearance skipped: {exc}", ok=False)

    # ── Voice Director ──
    with recorder.span("voice_director"):
        try:
            state.vo_direction = run_voice_director(state.av_script, state.brand)
            log_note(state, "voice_director", "VO direction ready")
        except Exception as exc:
            log_note(state, "voice_director", f"Voice director skipped: {exc}", ok=False)

    # ── Phase 4: Audio ──
    return _run_audio_phase(state, recorder)


def _run_from_writers_room(state: ProductionState, recorder: TraceRecorder) -> list:
    """Run writers room through audio. Returns captions list."""
    # ── Phase 2a: Writers Room ──
    with recorder.span("writers_room"):
        try:
            hooks, script = run_writers_room(
                state.effective_topic or state.topic,
                state.brand,
                state.creative_brief,
                state.duration_sec,
            )
        except Exception as exc:
            _fail(f"Writers room failed: {exc}", state, "writers_room")

        # Hook selection gate
        ok_hook, msg_hook = gate_hook_selection(hooks)
        if not ok_hook:
            _fail(msg_hook, state, "writers_room")
        log_note(state, "writers_room", msg_hook)
        state.hook_selection = hooks

        # AV script gate
        ok_script, msg_script = gate_av_script(
            script,
            budget=state.complexity_budget,
            retention=state.retention_beat_sheet,
        )
        if not ok_script:
            _fail(msg_script, state, "writers_room")
        state.av_script = script

        # Continuity Bible v1
        state.continuity_bible = ContinuityBible(
            canonical_vo_lines=[b.vo_line for b in script.beats],
            on_screen_text=[b.on_screen_text for b in script.beats if b.on_screen_text],
            claims=[state.effective_topic or state.topic],
            cta=script.cta,
            version=1,
        )
        evals = run_deterministic_evals(state, "writers_room")
        if any(not e.passed for e in evals):
            log_note(state, "writers_room",
                     f"Eval warnings: {[e.message for e in evals if not e.passed]}",
                     ok=False)
        log_note(state, "writers_room", "AV script approved")

    # ── Asset Research ──
    with recorder.span("asset_research"):
        try:
            state.asset_research = run_asset_research_crew(
                state.effective_topic or state.topic,
                state.brand,
                state.av_script,
            )
        except Exception as exc:
            log_note(state, "asset_research", f"Crew fallback: {exc}", ok=False)
            state.asset_research = build_queries_from_script(state)
        state.scene_images = resolve_scene_images(
            state, state.asset_research,
            remove_bg=state.brand.assets.remove_background if state.brand else False,
        )
        log_note(state, "asset_research",
                 f"{len(state.scene_images.assets)} scene images resolved")

    # ── Visual development through audio ──
    return _run_from_visual_dev(state, recorder)


def _run_render_phase(
    state: ProductionState,
    recorder: TraceRecorder,
    captions: list,
    *,
    render: bool = True,
) -> str | None:
    """Run post-production through render. Returns revision department name or None if QC passed."""
    # ── Phase 6: Post-production ──
    with recorder.span("postproduction"):
        try:
            captions_word_count = sum(
                len(seg.words) for seg in (captions or [])
            )
            pp_result = run_postproduction_crew(
                state.brand,
                state.av_script,
                state.composed_frames,
                state.audio_duration_sec or state.duration_sec,
                captions_word_count=captions_word_count,
            )
            state.post_brief = pp_result["post_brief"]
            state.edit_decisions = pp_result["edit_decisions"]
            state.motion_plan = pp_result["motion_plan"]
            state.color_grade = pp_result["color_grade"]
            state.sound_plan = pp_result["sound_plan"]
            state.caption_style = pp_result["caption_style"]
            state.video_spec = pp_result["video_spec"]
        except Exception as exc:
            _fail(f"Post-production crew failed: {exc}", state, "postproduction")

        # Wire audio, captions, and normalize scene types into video spec
        _normalize_scene_types(state)
        _wire_audio_to_spec(state, captions)
        # Wire SFX assets into video spec
        wire_sfx_to_spec(state)

        # Picture lock gate
        ok_lock, msg_lock, cert = gate_picture_lock(
            state.edit_decisions,
            state.audio_duration_sec or state.duration_sec,
            fps=state.brand.platform.fps,
            captions_word_count=captions_word_count,
        )
        if not ok_lock:
            _fail(msg_lock, state, "postproduction")
        state.picture_lock = cert
        log_note(state, "postproduction", msg_lock)
        # Save artifacts to disk
        _save_artifacts(state)

    # ── Storyboard Verification ──
    with recorder.span("storyboard"):
        if state.video_spec or state.composed_frames:
            try:
                stills = render_storyboard(state)
                if stills:
                    ok_story, msg_story, critique = gate_storyboard(
                        stills,
                        state.creative_brief,
                        state.brand,
                        state.composed_frames,
                    )
                    state.storyboard_stills = [str(s) for s in stills]
                    state.storyboard_critique = critique
                    if not ok_story:
                        log_note(state, "storyboard", msg_story, ok=False)
                        console.print(
                            f"[yellow]Storyboard verification issues: {msg_story}[/]"
                        )
                    else:
                        log_note(state, "storyboard", msg_story)
                else:
                    log_note(
                        state,
                        "storyboard",
                        "No storyboard frames rendered (remotion may not be available)",
                        ok=False,
                    )
            except Exception as exc:
                log_note(
                    state, "storyboard",
                    f"Storyboard verification failed: {exc}",
                    ok=False,
                )

    # ── Phase 7: QC ──
    with recorder.span("qc"):
        try:
            qc_result = run_qc_crew(
                state.video_spec,
                state.composed_frames,
                state.continuity_bible,
                state.av_script,
            )
            state.continuity_report = qc_result["continuity"]
            state.qc_verdict = qc_result["qc_verdict"]
        except Exception as exc:
            log_note(state, "qc", f"QC crew failed: {exc}", ok=False)
            state.qc_verdict = QCVerdict(passes=True, issues=[])

        ok_qc, msg_qc, dept = gate_qc(state, state.video_spec)
        if not ok_qc and dept and state.revision_count < 2:
            state.revision_count += 1
            log_note(state, "qc", f"Revision routed to {dept}", ok=False)
            return dept
        state.qc_passed = ok_qc
        log_note(state, "qc", msg_qc)

        # Clearance gate
        ok_clear, msg_clear = gate_clearance(
            state.sound_plan,
            state.illustration_plan,
            music_manifest_path=state.run_output().parent.parent / "assets" / "music" / "manifest.json",
        )
        if not ok_clear:
            log_note(state, "clearance", msg_clear, ok=False)
        else:
            log_note(state, "clearance", msg_clear)

    # ── Smoke Stills (pre-render fail-fast) ──
    if render and state.video_spec:
        with recorder.span("smoke_stills"):
            try:
                passed, msg, _ = smoke_test_stills(
                    run_output=state.run_output(),
                )
                log_note(state, "smoke_stills", msg, ok=passed)
                if not passed:
                    console.print(f"[yellow]Smoke stills: {msg}[/yellow]")
            except Exception as exc:
                log_note(state, "smoke_stills", f"Smoke stills check failed: {exc}", ok=False)
                console.print(f"[yellow]Smoke stills error (non-blocking): {exc}[/yellow]")

    # ── Render ──
    if render and state.video_spec:
        with recorder.span("render"):
            video_path = render_video(state)
            state.delivery = package_delivery(state, video_path)
            log_note(state, "delivery", f"Rendered {video_path}")


        # ── Dailies ──
        with recorder.span("dailies"):
            try:
                dailies_report = run_dailies(state, video_path=video_path)
                log_note(state, "dailies",
                         f"Passes={dailies_report.passes}, drift={dailies_report.drift_score:.3f}",
                         ok=dailies_report.passes)
                if not dailies_report.passes:
                    for issue in dailies_report.frame_comparisons:
                        desc = next(iter(issue.values()), str(issue))
                        log_note(state, "dailies", f"Dailies issue: {desc}", ok=False)
                        console.print(f"[yellow]Dailies: {desc}[/yellow]")
            except Exception as exc:
                log_note(state, "dailies", f"Dailies check failed: {exc}", ok=False)
                console.print(f"[yellow]Dailies error (non-blocking): {exc}[/yellow]")

        # ── Visual QA ──
        with recorder.span("visual_qa"):
            try:
                qa_result = run_visual_qa(state)
                if qa_result.get("revision_suggestions"):
                    console.print(
                        f"[bold cyan]Visual QA Critique[/bold cyan]\n{qa_result['revision_suggestions']}"
                    )
                    state.flywheel_context.append(
                        f"Visual QA: {qa_result['revision_suggestions'][:500]}"
                    )
            except Exception as exc:
                gating = state.strict_qa_override or (
                    state.brand is not None and state.brand.quality.strict_qa
                )
                if gating:
                    log_note(state, "visual_qa", f"Failed: {exc}", ok=False)
                    recorder.flush()
                    raise ProductionError(
                        f"Visual QA failed: {exc}",
                        phase="visual_qa",
                        hint="Fix visual issues or disable strict QA with --no-strict-qa.",
                    ) from exc
                console.print(f"[yellow]Visual QA failed (non-blocking): {exc}[/yellow]")
                log_note(state, "visual_qa", f"Failed: {exc}", ok=False)

    return None


def run_production(state: ProductionState, *, render: bool = True) -> ProductionState:
    if state.brand is None:
        _fail("Brand profile is not loaded", state, "setup", "Pass --brand or run crewai-remotion brand init")

    recorder = TraceRecorder(state.run_output())
    state.output_dir = str(state.run_output())
    run_dir = str(state.run_output())

    try:
        # ── Phase 0: Topic ──
        with recorder.span("topic"):
            state = run_topic_pipeline(state)
            log_note(state, "topic", f"effective_topic={state.effective_topic}")

        write_call_sheet(state, state.run_output() / "call_sheet.json")

        # ── Phase 1: Development ──
        with recorder.span("development"):
            try:
                brief, budget, beats = run_development_crew(
                    state.effective_topic or state.topic,
                    state.brand,
                    state.duration_sec,
                )
            except Exception as exc:
                _fail(f"Development crew failed: {exc}", state, "development",
                      "Verify OPENAI_API_KEY and model name in .env")
            state.creative_brief = brief
            state.complexity_budget = budget
            state.retention_beat_sheet = beats
            ok, msg = gate_creative_brief(state.creative_brief)
            if not ok:
                _fail(msg, state, "development")
            log_note(state, "development", msg)

        # ── Writers room through audio ──
        captions = _run_from_writers_room(state, recorder)

        # ── Revision loop: post-production through render ──
        while True:
            dept = _run_render_phase(state, recorder, captions, render=render)
            if dept is None:
                break  # QC passed
            if state.revision_count >= 2:
                break  # Max revisions reached; proceed with simplified delivery

            # Targeted revision routing: re-run only the affected phase and downstream
            if dept == "writers_room":
                captions = _run_from_writers_room(state, recorder)
            elif dept == "visual_development":
                captions = _run_from_visual_dev(state, recorder)
            # else: "postproduction" or default — loop continues, _run_render_phase handles it

        recorder.flush()

        # Persist learnings from this run into the flywheel
        try:
            save_lessons_from_state(state)
        except Exception:
            # Flywheel persistence is non-blocking
            pass

        return state

    except ProductionError:
        recorder.flush()
        raise
    except Exception as exc:
        recorder.flush()
        raise ProductionError(
            str(exc) or "Pipeline failed",
            phase="pipeline",
            hint="Re-run with --verbose. Check production_notes.jsonl in the run folder.",
            run_dir=run_dir,
        ) from exc


def _get_audio_duration(vo_path) -> float:
    """Get audio duration in seconds from WAV file."""
    try:
        import wave
        with wave.open(str(vo_path), 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / rate if rate > 0 else 0.0
    except Exception:
        return 0.0
