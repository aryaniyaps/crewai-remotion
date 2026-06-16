from __future__ import annotations

import json

from pathlib import Path

from crewai import Agent

from crewai_remotion.crews._common import _load_reference
from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.postproduction import (
    CaptionStyle,
    ColorPlan,
    EditDecisionListV2,
    MotionPlan,
    PostBrief,
    SoundPlan,
)
from crewai_remotion.models.video_spec import VideoSpec
from crewai_remotion.models.visual_development import ComposedFrames
from crewai_remotion.models.writers_room import AVScript


def run_postproduction_crew(
    brand: BrandProfile,
    script: AVScript,
    composed: ComposedFrames,
    audio_duration_sec: float,
    captions_word_count: int = 0,
) -> dict:
    """
    Post-production: Post Supervisor → Editor → Motion → Color → Sound → Captions → Mograph TD.

    Returns dict with keys: post_brief, edit_decisions, picture_lock, motion_plan,
    color_grade, sound_plan, caption_style, video_spec.
    """
    llm = get_llm()
    cuts_ref = _load_reference("cinematic_cuts.md")
    audio_ref = _load_reference("audio_edit_sync.md")
    motion_ref = _load_reference("motion_intent.md")
    color_ref = _load_reference("color.md")
    layout_ref = _load_reference("layout_vertical.md")
    comp_ref = _load_reference("composition.md")
    sfx_ref = _load_reference("sound_design.md")
    sfx_manifest = json.dumps(
        json.loads((Path(__file__).resolve().parents[4] / "assets" / "sfx" / "manifest.json").read_text()).get("sfx", []),
        indent=2,
    )

    script_json = script.model_dump_json()
    composed_json = composed.model_dump_json()
    fps = brand.platform.fps

    # ── Post Supervisor ──
    post_sup = Agent(
        role="Post Supervisor",
        goal="Brief the post-production crew — enforce no layout changes post-lock, set constraints",
        backstory="Post department head. You oversee the edit bay workflow. "
                  "Your brief is the contract for all post roles.",
        llm=llm,
        verbose=True,
    )
    post_brief: PostBrief = post_sup.kickoff(
        f"ComposedFrames: {composed_json}\n"
        f"AVScript: {script_json}\n"
        "Produce PostBrief with no_layout_changes=true, picture_lock_required=true, "
        "vo_primary_sync=true. Set motion_intensity from brand spec.",
        response_format=PostBrief,
    ).pydantic

    # ── Editor ──
    editor = Agent(
        role="Editor",
        goal="Lock picture timing — produce EditDecisionList with named cut types, "
             "Whisper-synced audio_sync_refs, and per-beat duration_frames",
        backstory=f"Primary cut authority. {cuts_ref[:600]} {audio_ref[:400]} "
                  "You work to real audio timestamps. No layout changes — you own timing only.",
        llm=llm,
        verbose=True,
    )
    edl: EditDecisionListV2 = editor.kickoff(
        f"AVScript beats: {script_json}\n"
        f"Audio duration: {audio_duration_sec}s at {fps}fps\n"
        f"Captions word count: {captions_word_count}\n"
        "For each beat boundary, produce a CutOut with: cut_type (from cinematic_cuts taxonomy), "
        "split_edit (none/j_cut/l_cut), audio_lead_frames (3-8 for j_cut), audio_trail_frames (6-15 for l_cut), "
        "audio_sync_ref (phrase_id or word_id), audio_sync_event (phrase_end/emphasis_word/downbeat). "
        "Default rhythm: j_cut into hook, hard_cut between body points, l_cut into CTA. Max 1 smash_cut per 30s. "
        "Beat durations as list of {beat_id, frames}. Sum of frames must equal ceil(audio_duration_sec * fps).",
        response_format=EditDecisionListV2,
    ).pydantic

    # ── Motion Designer ──
    motion_designer = Agent(
        role="Motion Designer",
        goal="Map Editor's cut types to Remotion transition tokens + in-beat motion peaks. "
             "Never change layout or timing.",
        backstory=f"{motion_ref[:500]} You implement the Editor's cuts as animations. "
                  "Pick snappy/smooth/kinetic springs from the brand preset. "
                  "Set cut_on_action_frames at ~70% of exit animation for cut_on_action cuts.",
        llm=llm,
        verbose=True,
    )
    motion_plan: MotionPlan = motion_designer.kickoff(
        f"EditDecisionList: {edl.model_dump_json()}\n"
        f"Brand motion style: {brand.visual.motion_style}\n"
        f"ComposedFrames motion_intents: {json.dumps([{'beat_id': f.beat_id, 'motion': f.motion_intent} for f in composed.frames])}\n"
        "Produce MotionPlan with global_style, transition_tokens per beat-boundary, "
        "cut_on_action_frames for any cut_on_action cuts, stagger_ms.",
        response_format=MotionPlan,
    ).pydantic

    # ── Colorist ──
    colorist = Agent(
        role="Colorist",
        goal="Set per-beat color grading: accent emphasis, background saturation, text contrast tier",
        backstory=f"{color_ref[:500]} You grade each beat for emotion and readability. "
                  "Never change the brand palette — you adjust application only.",
        llm=llm,
        verbose=True,
    )
    color_grade: ColorPlan = colorist.kickoff(
        f"Brand palette: primary={brand.visual.primary}, secondary={brand.visual.secondary}, "
        f"accent={brand.visual.accent}, surface={brand.visual.surface}\n"
        f"ComposedFrames background_variants: {json.dumps([{'beat_id': f.beat_id, 'bg': f.background_variant} for f in composed.frames])}\n"
        "Per beat: bg_saturation (0-1), accent_boost (0-1), text_contrast_tier (high/aa/fail — never fail). "
        "Hook beats: full saturation. Body: muted. Stats: accent boost. CTA: moderate.",
        response_format=ColorPlan,
    ).pydantic

    # ── Sound Designer ──
    sound_designer = Agent(
        role="Sound Designer",
        goal="Select music track, mark sync downbeats, cue SFX on cuts per SFX_BRIDGE, set ducking curve",
        backstory=f"{sfx_ref} {audio_ref[:300]} "
                  "You design for TikTok/Reels: cuts drive SFX, whoosh transitions are the backbone, "
                  "impact on reveals, silence on dissolves and invisible cuts. "
                  "VO is primary — every SFX must survive the question: 'Does this help the cut land, "
                  "or is it noise?' Music ducks under speech; SFX duck under both.",
        llm=llm,
        verbose=True,
    )
    sound_plan: SoundPlan = sound_designer.kickoff(
        f"Music mood: {brand.audio.music_mood}, volume: {brand.audio.music_volume}\n"
        f"EditDecisionList: {edl.model_dump_json()}\n"
        f"Available SFX catalog: {sfx_manifest}\n"
        "Pick music_track_id from mood, estimate BPM. "
        "Mark sync_markers[] with frame, event (downbeat/snare/phrase_start), "
        "use_for (major_cut/accent_only). "
        "Cue sfx_cues[] per the SFX_BRIDGE mapping: "
        "hard_cut/j_cut/l_cut/dissolve/invisible_cut → no SFX; "
        "jump_cut/cross_cut → whoosh; match_cut/montage → whoosh_low; "
        "smash_cut → impact (may add whoosh/rise as second cue 6-12 frames before); "
        "cut_on_action → swoosh. "
        "STRICT: max 1 SFX cue per beat (smash_cut may have 2). "
        "No SFX on dissolve or invisible_cut — ever. "
        "Montage: whoosh_low every 2-3 items, not every item. "
        "SFX volume 0.5-0.8; place in VO pauses or at beat boundaries. "
        "Set ducking_curve: music at 0.25 normally, duck to 0.10 under VO beats.",
        response_format=SoundPlan,
    ).pydantic

    # ── Caption Designer ──
    caption_designer = Agent(
        role="Caption Designer",
        goal="Set caption style — TikTok-native rhythm with word highlight, respecting headline zones",
        backstory=f"{layout_ref[:300]} You format captions for mobile readability. "
                  "Position must avoid headline_zone and danger zones. "
                  "Use caption_highlight color for current-word karaoke emphasis.",
        llm=llm,
        verbose=True,
    )
    caption_style: CaptionStyle = caption_designer.kickoff(
        f"Brand caption_highlight: {brand.visual.caption_highlight}\n"
        f"Font: {brand.visual.font_body}\n"
        f"ComposedFrames headline zones and safe margins\n"
        "Set combine_ms=800, highlight_color from brand, position=bottom. "
        "Tier=caption. Ensure no collision with headline zones.",
        response_format=CaptionStyle,
    ).pydantic

    # ── Mograph TD ──
    mograph_td = Agent(
        role="Mograph TD",
        goal="Assemble VideoSpec from ComposedFrames + all post artifacts while preserving subject assets. "
             "Never override composition — implement only what was approved.",
        backstory="Motion graphics technical director. You build the Remotion comp from approved boards. "
                  "You map agent tokens to Remotion primitives, including SceneSubjectLayer semantic illustration ids. "
                  "You preserve subject assets exactly and make motion graphics support the subject instead of replacing it. "
                  "You flag conflicts, never resolve them silently.",
        llm=llm,
        verbose=True,
    )

    scenes_json = json.dumps([
        {
            "id": f.beat_id,
            "type": f.scene_type,
            "headline": f.headline,
            "subhead": f.subhead,
            "illustration_id": f.illustration_id,
            "image_path": f.image_path,
            "background_variant": f.background_variant,
            "layout": f.layout,
            "motion_intent": f.motion_intent,
        }
        for f in composed.frames
    ])

    video_spec: VideoSpec = mograph_td.kickoff(
        f"ComposedFrames: {scenes_json}\n"
        f"EditDecisionList: {edl.model_dump_json()}\n"
        f"MotionPlan: {motion_plan.model_dump_json()}\n"
        f"Audio duration: {audio_duration_sec}s at {fps}fps\n"
        f"Brand theme: primary={brand.visual.primary}, secondary={brand.visual.secondary}, "
        f"accent={brand.visual.accent}, surface={brand.visual.surface}, "
        f"caption_highlight={brand.visual.caption_highlight}, "
        f"font_heading={brand.visual.font_heading}, font_body={brand.visual.font_body}, "
        f"motion_style={brand.visual.motion_style}, texture={brand.visual.texture}\n"
        "Assemble full VideoSpec. Per beat: id, type, headline, subhead, duration_frames (from EDL), "
        "illustration_id, image_path, background_variant, layout, motion_intent, cut_type (from EDL), "
        "motion_intensity (low/medium/high — hook=high, body=medium, cta=low), "
        "parallax_depth (0-1, use 0.3 for body beats), camera_motion (push_in for hook, pan_left/right for body, none for cta).\n"
        "STRICT subject preservation: copy image_path exactly from ComposedFrames whenever present; do not drop, rewrite, or replace it. "
        "When image_path is empty, copy the semantic illustration_id exactly from ComposedFrames so SceneSubjectLayer can render ids like data_center, server_rack, power_grid, chip, globe_network, or city_buildings. "
        "Every scene must carry either image_path or illustration_id when ComposedFrames provided one.\n"
        "Set motion_intent per beat from enter_up, slide_in, scale_burst, fade_in. Preserve approved ComposedFrames intent when it is already varied; if intents are missing or all the same, choose a varied sequence that fits beat type (hook scale_burst, body slide_in/enter_up alternation, stat scale_burst, rehook fade_in, cta enter_up). Do not output all enter_up.\n"
        "For motion_graphics: assign 1-2 accent graphics per beat that support the subject and selected motion_intent without covering it — "
        "hook: particles+ring_pulse around subject, body: wave+data_flow behind/along subject edges, stat: energy_burst+orbital around subject, rehook: grid_pulse behind subject, cta: kinetic_type_zoom as text accent only. "
        "The config field on each graphic MUST be a single-line JSON string like '{\"count\":20,\"speed\":0.4,\"color\":\"primary\"}'. "
        "Set theme from brand. Leave audio fields empty — music/voiceover paths are wired separately. "
        "Duration frames = sum of beat durations from EDL. "
        "Set width=1080, height=1920, fps from brand.",
        response_format=VideoSpec,
    ).pydantic
    return {
        "post_brief": post_brief,
        "edit_decisions": edl,
        "picture_lock": None,  # Set by gate after this returns
        "motion_plan": motion_plan,
        "color_grade": color_grade,
        "sound_plan": sound_plan,
        "caption_style": caption_style,
        "video_spec": video_spec,
    }
