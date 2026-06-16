from __future__ import annotations

import json
import re

from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.cinematic_cuts import CutType, EditDecision, EditDecisionList
from crewai_remotion.models.development import (
    ComplexityBudget,
    CreativeBrief,
    DepartmentKickoffMemo,
    RetentionBeatSheet,
)
from crewai_remotion.models.postproduction import MotionPlan, SoundPlan, VODirection
from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.models.video_spec import SceneSpec, ThemeTokens, VideoSpec
from crewai_remotion.models.visual_development import (
    ComposedFrame,
    ComposedFrames,
    EnvironmentPlan,
    IllustrationPlan,
    IllustrationSlot,
    StyleBible,
    StyleFrameSpec,
    TypeSpec,
)
from crewai_remotion.models.writers_room import AVBeat, AVScript, ContinuityBible, HookCandidate, HookSelection


def phase_development(state: ProductionState) -> ProductionState:
    topic = state.effective_topic or state.topic
    brand = state.brand
    assert brand is not None

    max_beats = max(3, min(6, int(state.duration_sec / 6)))
    state.complexity_budget = ComplexityBudget(
        max_beats=max_beats,
        max_lottie_slots=3,
        max_motion_layers=4,
        max_words_vo=int(state.duration_sec * 3),
        approved=True,
    )
    state.retention_beat_sheet = RetentionBeatSheet(
        beats=["hook", "context", "value_1", "value_2", "cta"],
        hook_window_sec=3.0,
        pattern_interrupts=["stat", "question"],
    )
    state.creative_brief = CreativeBrief(
        objective=f"Educate viewers on: {topic}",
        audience="social media scrollers",
        key_message=topic,
        tone_notes=", ".join(brand.voice.tone),
        cta="Follow for more",
        approved=True,
    )
    state.kickoff_memo = DepartmentKickoffMemo(
        writers_room=f"Hook in 3s. Tone: {', '.join(brand.voice.tone)}",
        visual_development=f"Motion: {brand.visual.motion_style}. Colors from brand palette.",
        post_production="VO-primary sync. Hard cuts on phrase boundaries.",
    )
    return state


def phase_writers_room(state: ProductionState) -> ProductionState:
    topic = state.effective_topic or state.topic
    brand = state.brand
    assert brand is not None

    hooks = [
        HookCandidate(id="h1", text=f"Stop scrolling — {topic.split('—')[0].strip()}", pattern="question", score=0.9),
        HookCandidate(id="h2", text=f"3 tools that changed how I work", pattern="stat-shock", score=0.85),
        HookCandidate(id="h3", text=f"Founders are sleeping on this", pattern="contrarian", score=0.8),
    ]
    state.hook_selection = HookSelection(candidates=hooks, selected_id="h1", rationale="Strongest pattern interrupt")

    selected = next(h for h in hooks if h.id == state.hook_selection.selected_id)
    beats = _build_beats_from_topic(topic, selected.text, state.duration_sec)
    state.av_script = AVScript(
        title=topic[:60],
        hook=selected.text,
        beats=beats,
        cta="Follow for more tips",
        total_duration_sec=state.duration_sec,
        approved=True,
    )
    state.continuity_bible = ContinuityBible(
        canonical_vo_lines=[b.vo_line for b in beats],
        on_screen_text=[b.on_screen_text for b in beats if b.on_screen_text],
        claims=[topic],
        cta="Follow for more tips",
        version=1,
    )
    return state


def _build_beats_from_topic(topic: str, hook: str, duration: float) -> list[AVBeat]:
    """Build a structurally sound beat list from free-text topic using sentence-aware extraction."""
    raw = re.split(r"(?<=[.!?])\s+", topic)
    sentences = [s.strip() for s in raw if len(s.strip()) > 3]
    if not sentences:
        sentences = [topic.strip()] if topic and topic.strip() else ["Exploring new ideas"]

    # Detect numeric content for a stat-style beat
    numbers = re.findall(r"\b\d+[%x×]?\b", topic)
    has_numeric = len(numbers) > 0

    # Rank sentences by "interestingness" — length, specificity, numeric hooks
    def _score(s: str) -> float:
        sc = min(len(s.split()) / 8.0, 1.0)
        if re.search(r"\d", s):
            sc += 0.25
        if re.search(r"\b[A-Z][a-z]{2,}\b", s):
            sc += 0.15
        return sc

    ranked = sorted(sentences, key=_score, reverse=True)
    body_count = max(1, min(4, int(duration / 8)))
    body_sentences = ranked[:body_count]

    beats: list[AVBeat] = []

    # b0 — Hook: the grabber
    beats.append(
        AVBeat(
            beat_id="b0",
            beat_type="hook",
            vo_line=hook,
            on_screen_text=hook[:40] if len(hook) > 40 else hook,
            visual_intent="Bold kinetic title card — large type slams center frame with motion-blur entrance and glow bloom",
            duration_hint_sec=3.0,
        )
    )

    # Body beats from best sentences
    visual_palette = [
        "Split-screen product demo with animated cursor highlights and smooth zoom cuts between panels",
        "Animated diagram building up layer by layer on a dark gradient — each element fades in on beat",
        "Talking-head frame with floating key terms popping in at screen edges, pulsing on emphasis",
        "Full-bleed b-roll with overlaid bullet points stacking vertically, each snapping in with a slide",
    ]
    for i, sent in enumerate(body_sentences):
        vo = sent if len(sent) <= 90 else sent[:87] + "..."
        on_screen = sent[:50] if len(sent) > 50 else sent
        beats.append(
            AVBeat(
                beat_id=f"b{i + 1}",
                beat_type="point",
                vo_line=vo,
                on_screen_text=on_screen,
                visual_intent=visual_palette[i % len(visual_palette)],
                duration_hint_sec=round(max(4.0, min(7.0, len(vo) * 0.075)), 1),
            )
        )

    # Stat beat — insert after first body point when numeric data is present
    if has_numeric and len(beats) >= 2:
        best_num = max(numbers, key=len)
        insert_at = min(2, len(beats))
        beats.insert(
            insert_at,
            AVBeat(
                beat_id="b-stat",
                beat_type="stat",
                vo_line=f"The numbers tell the story — {best_num} is the difference that matters.",
                on_screen_text=best_num,
                visual_intent=(
                    f"Massive animated stat — \"{best_num}\" scales up center-frame with bold condensed type, "
                    "particle burst behind, camera push-in"
                ),
                duration_hint_sec=5.0,
            ),
        )

    # Renumber beats sequentially
    for j, b in enumerate(beats):
        b.beat_id = f"b{j}"

    # CTA — always closes the video
    beats.append(
        AVBeat(
            beat_id=f"b{len(beats)}",
            beat_type="cta",
            vo_line="Follow for more tips.",
            on_screen_text="Follow →",
            visual_intent="Clean CTA card — brand logo reveal, follow button with pulse animation, gradient wipe to black",
            duration_hint_sec=4.0,
        )
    )

    return beats


def phase_visual_development(state: ProductionState) -> ProductionState:
    brand = state.brand
    script = state.av_script
    assert brand is not None and script is not None

    state.style_bible = StyleBible(
        mood_keywords=[brand.visual.motion_style, *brand.voice.tone[:2]],
        do_list=["rule of thirds", "high contrast captions", "one focal point per beat"],
        dont_list=["centered wall of text", "more than 8 words on screen"],
    )
    state.style_frames = [
        StyleFrameSpec(beat_id=b.beat_id, mood=brand.visual.motion_style, approved=True)
        for b in script.beats
    ]
    state.environment_plan = EnvironmentPlan(
        background_style="gradient_mesh",
        depth_layers=2,
        texture=brand.visual.texture,
    )
    state.type_spec = TypeSpec(max_words_headline=8)
    state.illustration_plan = IllustrationPlan(
        slots=[
            IllustrationSlot(beat_id=b.beat_id, catalog_id=f"icon_{b.beat_type}", position="right")
            for b in script.beats
            if b.beat_type in ("point", "stat")
        ]
    )

    scene_map = {
        "hook": "HookBeat",
        "point": "PointBeat",
        "stat": "StatBeat",
        "quote": "QuoteBeat",
        "cta": "CTABeat",
    }
    frames = []
    for b in script.beats:
        frames.append(
            ComposedFrame(
                beat_id=b.beat_id,
                scene_type=scene_map.get(b.beat_type, "PointBeat"),
                headline=b.on_screen_text or b.vo_line[:40],
                subhead=b.vo_line if b.on_screen_text else "",
                illustration_id=f"icon_{b.beat_type}" if b.beat_type in ("point", "stat") else None,
                background_variant="primary" if b.beat_type == "hook" else "secondary",
                layout="left_stack" if b.beat_id[-1] in "135" else "right_stack",
                motion_intent="enter_up" if brand.visual.motion_style == "snappy" else "fade_in",
            )
        )
    state.composed_frames = ComposedFrames(frames=frames, approved=True)
    return state


def phase_postproduction(state: ProductionState) -> ProductionState:
    brand = state.brand
    script = state.av_script
    frames = state.composed_frames
    assert brand and script and frames

    fps = brand.platform.fps
    total_sec = script.total_duration_sec
    beat_secs = [b.duration_hint_sec for b in script.beats]
    total_hint = sum(beat_secs) or total_sec
    scale = total_sec / total_hint

    decisions = []
    scenes: list[SceneSpec] = []
    cursor = 0
    cut_types = [CutType.HARD_CUT, CutType.JUMP_CUT, CutType.SMASH_CUT, CutType.L_CUT, CutType.HARD_CUT]

    for i, (beat, frame) in enumerate(zip(script.beats, frames.frames)):
        dur_sec = beat.duration_hint_sec * scale
        dur_frames = max(int(dur_sec * fps), fps)
        ct = cut_types[i % len(cut_types)]
        decisions.append(EditDecision(scene_id=beat.beat_id, cut_type=ct))
        image_path = frame.image_path
        if not image_path and state.scene_images:
            asset = state.scene_images.for_beat(beat.beat_id)
            if asset:
                image_path = asset.public_path
        scenes.append(
            SceneSpec(
                id=beat.beat_id,
                type=frame.scene_type,
                headline=frame.headline,
                subhead=frame.subhead,
                duration_frames=dur_frames,
                illustration_id=frame.illustration_id,
                image_path=image_path,
                background_variant=frame.background_variant,
                layout=frame.layout,
                motion_intent=frame.motion_intent,
                cut_type=ct,
            )
        )
        cursor += dur_frames

    state.edit_decisions = EditDecisionList(decisions=decisions, pacing_notes="VO-primary phrase cuts")
    state.motion_plan = MotionPlan(global_style=brand.visual.motion_style)
    state.sound_plan = SoundPlan(music_track_id=f"mood_{brand.audio.music_mood}", music_volume=brand.audio.music_volume)
    state.vo_direction = VODirection(pacing="conversational", emphasis_words=[script.hook.split()[0]])

    theme = ThemeTokens(
        primary=brand.visual.primary,
        secondary=brand.visual.secondary,
        accent=brand.visual.accent,
        surface=brand.visual.surface,
        caption_highlight=brand.visual.caption_highlight,
        font_heading=brand.visual.font_heading,
        font_body=brand.visual.font_body,
        motion_style=brand.visual.motion_style,
        texture=brand.visual.texture,
    )
    state.video_spec = VideoSpec(
        title=script.title,
        width=brand.platform.width,
        height=brand.platform.height,
        fps=fps,
        duration_frames=cursor,
        theme=theme,
        scenes=scenes,
        edit_decisions=state.edit_decisions,
        audio={"music_mood": brand.audio.music_mood, "music_volume": brand.audio.music_volume},
    )
    return state


def save_artifacts(state: ProductionState) -> None:
    out = state.run_output()
    if state.video_spec:
        (out / "video_spec.json").write_text(
            json.dumps(state.video_spec.to_remotion_props(), indent=2),
            encoding="utf-8",
        )
    if state.av_script:
        (out / "av_script.json").write_text(state.av_script.model_dump_json(indent=2), encoding="utf-8")
    if state.creative_brief:
        (out / "creative_brief.json").write_text(state.creative_brief.model_dump_json(indent=2), encoding="utf-8")
