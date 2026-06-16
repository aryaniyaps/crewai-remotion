from __future__ import annotations

import json

from crewai import Agent

from crewai_remotion.crews._common import _load_reference
from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.visual_development import (
    ComposedFrames,
    IllustrationPlan,
    StyleBible,
    StyleFrameSpecs,
    TypeSpec,
)
from crewai_remotion.models.writers_room import AVScript


def run_visual_development(
    brand: BrandProfile,
    script: AVScript,
    image_manifest_json: str = "",
) -> dict:
    """
    Visual Development: RefLib → Art Director → Style Frames → parallel(PD, TypoDir, Ilus) → Storyboard → Compositor.

    Returns dict with: mood_board, style_bible, style_frame_specs, environment_plan,
    type_spec, illustration_plan, rough_storyboard, composed_frames.
    """
    llm = get_llm()
    comp_ref = _load_reference("composition.md")
    layout_ref = _load_reference("layout_vertical.md")
    typo_ref = _load_reference("typography.md")
    color_ref = _load_reference("color.md")
    motion_ref = _load_reference("motion_intent.md")
    cuts_ref = _load_reference("cinematic_cuts.md")

    script_json = script.model_dump_json()
    image_info = image_manifest_json if image_manifest_json else "[]"

    # ── Reference Librarian ──
    librarian = Agent(
        role="Reference Librarian",
        goal="Curate mood board from brand assets and aesthetic keywords — give Art Director concrete anchors",
        backstory="You research visual references and curate mood boards. "
                  f"Brand: {brand.name}, colors: {brand.visual.primary}/{brand.visual.secondary}. "
                  "No copy, no layout — references only.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import MoodBoard
    mood_board: MoodBoard = librarian.kickoff(
        f"Brand: {brand.model_dump_json()}\n"
        f"AVScript beat types: {json.dumps([{'id': b.beat_id, 'type': b.beat_type} for b in script.beats])}\n"
        "Curate 5-10 MoodReferences. Each: tag (e.g. 'bold_tech', 'minimal_dark'), "
        "rationale (1 sentence), apply_to_beats (list of beat_ids). "
        "Keywords should reflect the brand's motion_style and visual palette.",
        response_format=MoodBoard,
    ).pydantic

    # ── Art Director ──
    art_director = Agent(
        role="Art Director",
        goal="Produce style bible from mood board + creative brief. Create 2 style frame specs for CD approval.",
        backstory=f"{color_ref[:400]} You own the visual identity for this piece. "
                  f"Motion: {brand.visual.motion_style}, texture: {brand.visual.texture}. "
                  "Your style frames are the contract for all downstream visual work.",
        llm=llm,
        verbose=True,
    )
    style_bible: StyleBible = art_director.kickoff(
        f"MoodBoard: {mood_board.model_dump_json()}\n"
        f"Brand: {brand.model_dump_json()}\n"
        f"AVScript: {script_json}\n"
        "Produce StyleBible with mood_keywords, do_list, dont_list, color_emphasis, texture. "
        "Then produce StyleFrameSpecs with 2 frames: one hook beat, one mid-video beat. "
        "Each frame: beat_id, mood, color_emphasis, layout_notes, font_tier, illustration_slot, approved=true.",
        response_format=StyleBible,
    ).pydantic

    # Style frame specs (separate call — CD approval gate)
    style_frames: StyleFrameSpecs = art_director.kickoff(
        f"StyleBible: {style_bible.model_dump_json()}\n"
        f"AVScript beats: {script_json}\n"
        "Create StyleFrameSpecs with 2 frames. Hook beat (first beat) + mid beat (beat at ~50% duration). "
        "Mark both approved=true for initial pass.",
        response_format=StyleFrameSpecs,
    ).pydantic

    # ── Production Designer ──
    from crewai_remotion.models.visual_development import EnvironmentPlan
    pd = Agent(
        role="Production Designer",
        goal="Design backgrounds, depth layers, and atmosphere per beat — gradient direction, texture density",
        backstory=f"Motion style: {brand.visual.motion_style}. "
                  "You create the visual environment — the world the content lives in. "
                  "Each beat needs a distinct but cohesive background.",
        llm=llm,
        verbose=True,
    )
    environment_plan: EnvironmentPlan = pd.kickoff(
        f"AVScript: {script_json}\n"
        f"StyleBible: {style_bible.model_dump_json()}\n"
        f"Brand texture: {brand.visual.texture}\n"
        "Per beat: background_type (gradient_mesh/solid/radial), depth_layers (1-3), "
        "gradient_direction (top_to_bottom/bottom_to_top/diagonal), atmospheric_density (0-1). "
        "Hook beats: more texture. Body beats: cleaner. CTA: fade to surface.",
        response_format=EnvironmentPlan,
    ).pydantic

    # ── Typography Director ──
    type_director = Agent(
        role="Typography Director",
        goal="Set type hierarchy per beat — tier, weight contrast, alignment, emphasis words",
        backstory=f"{typo_ref[:500]} Font: {brand.visual.font_heading}/{brand.visual.font_body}, "
                  f"weights: {brand.visual.font_weights}. Max 8 words on screen per beat.",
        llm=llm,
        verbose=True,
    )
    type_spec: TypeSpec = type_director.kickoff(
        f"AVScript beats: {script_json}\n"
        f"StyleBible: {style_bible.model_dump_json()}\n"
        "Per beat: tier (display/headline/body/caption), weight_contrast (≥200), "
        "alignment (left/center/right), max_lines (1-2), emphasis_words (1-2 per beat). "
        "Hook: display tier. Body: headline tier. CTA: headline tier. Never center body text.",
        response_format=TypeSpec,
    ).pydantic

    # ── Illustrator ──
    illustrator = Agent(
        role="Illustrator",
        goal="Define one concrete animated subject slot per beat using photo assets or semantic flat-vector ids",
        backstory=f"Brand palette: primary={brand.visual.primary}, accent={brand.visual.accent}. "
                  "Every beat needs a dominant subject that can be animated in a polished flat/vector educational style. "
                  "Use Available images when they contain a useful beat-specific subject; otherwise choose semantic ids only, "
                  "such as data_center, server_rack, power_grid, chip, globe_network, city_buildings, robot_arm, factory, chart_stack. "
                  "Motion graphics are accents, never the subject.",
        llm=llm,
        verbose=True,
    )
    illustration_plan: IllustrationPlan = illustrator.kickoff(
        f"AVScript beats: {script_json}\n"
        f"Available images: {image_info}\n"
        f"Brand Lottie overrides: {json.dumps(brand.assets.lottie_overrides)}\n"
        "Per beat, create exactly one concrete subject slot: asset_type (photo when Available images has a useful subject, otherwise lottie/svg/shape), "
        "catalog_id (for non-photo slots use a semantic subject id such as data_center, server_rack, power_grid, chip, globe_network, city_buildings; for photo slots reference the exact available image path/id), "
        "placement_zone (tl/tr/ml/mr/bl/br/center), scale_tier (sm/md/lg). "
        "The subject must be a real object/entity implied by the beat text, not abstract waves, blobs, particles, or background texture. Max 3 lottie slots total.",
        response_format=IllustrationPlan,
    ).pydantic

    # ── Storyboard Artist ──
    from crewai_remotion.models.visual_development import RoughStoryboard
    storyboard = Agent(
        role="Storyboard Artist",
        goal="Plan beat-by-beat narrative: action, camera notes, cut type intent, audio sync hints",
        backstory=f"{cuts_ref[:500]} {motion_ref[:300]} "
                  "You plan what happens in each beat and how transitions connect them. "
                  "Intent only — Editor finalizes timing.",
        llm=llm,
        verbose=True,
    )
    rough_storyboard: RoughStoryboard = storyboard.kickoff(
        f"AVScript: {script_json}\n"
        f"StyleBible: {style_bible.model_dump_json()}\n"
        "Per beat: action (what happens visually), camera_notes, "
        "cut_type_intent (from cinematic_cuts taxonomy), audio_sync_hint. "
        "Default rhythm: j_cut into hook, hard_cut between body, l_cut into CTA.",
        response_format=RoughStoryboard,
    ).pydantic

    # ── Compositor ──
    compositor = Agent(
        role="Compositor",
        goal="Compose final frame layout around a dominant concrete subject while preserving approved image/illustration choices",
        backstory=f"{comp_ref[:600]} {layout_ref[:400]} "
                  f"Brand text_density: {brand.visual.text_density}. "
                  "You are the final authority on screen composition. "
                  "Every beat: one dominant subject in the upper/mid frame, one focal point, declared zones, negative space ratio ≥ 0.25, safe margins. "
                  "Captions carry narration, so scene text must stay short and must not collide with the bottom caption area.",
        llm=llm,
        verbose=True,
    )
    composed_frames: ComposedFrames = compositor.kickoff(
        f"AVScript beats: {script_json}\n"
        f"Available images: {image_info}\n"
        f"TypeSpec: {type_spec.model_dump_json()}\n"
        f"IllustrationPlan: {illustration_plan.model_dump_json()}\n"
        f"EnvironmentPlan: {environment_plan.model_dump_json()}\n"
        f"RoughStoryboard: {rough_storyboard.model_dump_json()}\n"
        f"Layout rules: {layout_ref}\n"
        "Per beat: scene_type from beat_type, headline, subhead, "
        "focal_point (tl/tr/ml/mr/bl/br/center — never all center), "
        "headline_zone, illustration_zone, logo_zone, "
        "negative_space_ratio (≥0.25 for minimal text_density), "
        "balance_notes, safe_margin_ok=true, "
        "illustration_id, image_path, "
        "background_variant, layout, motion_intent. "
        "If Available images contains a usable asset for the beat_id, copy its exact public_path/image_path into image_path and do not discard it. "
        "If no photo is ideal, set image_path=null and set illustration_id to a semantic SceneSubjectLayer id from the IllustrationPlan/catalog_id such as data_center, server_rack, power_grid, chip, globe_network, city_buildings, robot_arm, factory, or chart_stack. "
        "headline must be 3-5 words max and subhead 0-4 words; never duplicate the full narration because captions carry the sentence text. "
        "Keep headline zones away from bottom captions; when captions exist, the subject owns upper/mid frame. "
        "Choose varied motion_intent by beat from enter_up, slide_in, scale_burst, fade_in rather than repeating one value. "
        "Alternate layout between consecutive beats. approved=true.",
        response_format=ComposedFrames,
    ).pydantic

    return {
        "mood_board": mood_board,
        "style_bible": style_bible,
        "style_frame_specs": style_frames,
        "environment_plan": environment_plan,
        "type_spec": type_spec,
        "illustration_plan": illustration_plan,
        "rough_storyboard": rough_storyboard,
        "composed_frames": composed_frames,
    }
