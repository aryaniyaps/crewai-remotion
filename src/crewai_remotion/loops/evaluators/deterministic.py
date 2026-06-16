"""Deterministic evaluators — schema, cut sync, safe zones, retention coverage.

These run after every phase. Maker ≠ checker: these are NOT the producing agents.
"""

from __future__ import annotations
from dataclasses import dataclass

from crewai_remotion.models.production_state import ProductionState


@dataclass
class EvalResult:
    name: str
    passed: bool
    message: str
    score: float = 0.0
    department: str = ""


def run_deterministic_evals(state: ProductionState, phase: str) -> list[EvalResult]:
    """Run all deterministic evals for a given phase."""
    results: list[EvalResult] = []

    if phase == "development":
        results.extend(_eval_creative_brief(state))
    elif phase == "writers_room":
        results.extend(_eval_writers_room(state))
    elif phase == "visual_development":
        results.extend(_eval_visual_development(state))
    elif phase == "postproduction":
        results.extend(_eval_postproduction(state))
    elif phase == "qc":
        results.extend(_eval_qc(state))

    return results


# ── Development ──

def _eval_creative_brief(state: ProductionState) -> list[EvalResult]:
    results = []
    brief = state.creative_brief
    if not brief:
        return [EvalResult("brief_exists", False, "No creative brief", department="development")]

    required = ["objective", "audience", "key_message", "cta"]
    missing = [f for f in required if not getattr(brief, f, None)]
    results.append(EvalResult(
        "brief_completeness",
        len(missing) == 0,
        f"Missing: {missing}" if missing else "All required fields present",
        score=1.0 - (len(missing) / len(required)),
        department="development",
    ))

    budget = state.complexity_budget
    if budget:
        ok = budget.max_beats >= 3 and budget.max_beats <= 8
        results.append(EvalResult(
            "complexity_budget_range",
            ok,
            f"max_beats={budget.max_beats} (expected 3-8)",
            department="development",
        ))

    return results


# ── Writers Room ──

def _eval_writers_room(state: ProductionState) -> list[EvalResult]:
    results = []
    script = state.av_script
    if not script:
        return [EvalResult("script_exists", False, "No AV script", department="writers_room")]

    # Beat count
    beat_count = len(script.beats)
    budget = state.complexity_budget
    max_beats = budget.max_beats if budget else 8
    ok_beats = beat_count >= 2 and beat_count <= max_beats
    results.append(EvalResult(
        "beat_count",
        ok_beats,
        f"{beat_count} beats (max {max_beats})",
        department="writers_room",
    ))

    # Beat rhythm — warn if all beats share the same duration
    durations = {b.duration_hint_sec for b in script.beats}
    if len(durations) == 1 and beat_count >= 3:
        results.append(EvalResult(
            "beat_rhythm",
            False,
            f"All {beat_count} beats are {list(durations)[0]}s — vary pacing for retention",
            score=0.5,
            department="writers_room",
        ))

    # Hook exists and is ≤ 3.5s
    hooks = [b for b in script.beats if b.beat_type == "hook"]
    if hooks:
        hook_ok = hooks[0].duration_hint_sec <= 3.5
        results.append(EvalResult(
            "hook_duration",
            hook_ok,
            f"Hook: {hooks[0].duration_hint_sec}s (max 3.5s)",
            department="writers_room",
        ))

    # Hook on-screen text must not be empty
    if hooks:
        hook_text = hooks[0].on_screen_text
        hook_wc = len(hook_text.split()) if hook_text else 0
        if hook_wc == 0:
            results.append(EvalResult(
                "hook_on_screen_text",
                False,
                "Hook beat has empty on_screen_text — viewer sees nothing",
                department="writers_room",
            ))
        elif hook_wc > 8:
            results.append(EvalResult(
                "hook_on_screen_text",
                False,
                f"Hook: {hook_wc} on-screen words (max 8)",
                department="writers_room",
            ))
        else:
            results.append(EvalResult(
                "hook_on_screen_text",
                True,
                f"Hook: {hook_wc} on-screen words",
                department="writers_room",
            ))

    # Word count per beat (on-screen)
    for beat in script.beats:
        wc = len(beat.on_screen_text.split()) if beat.on_screen_text else 0
        if wc > 8:
            results.append(EvalResult(
                "word_cap_per_beat",
                False,
                f"{beat.beat_id}: {wc} on-screen words (max 8)",
                department="writers_room",
            ))

    # Word economy — warn if any beat is wordy
    for beat in script.beats:
        wc = len(beat.on_screen_text.split()) if beat.on_screen_text else 0
        if wc > 12:
            results.append(EvalResult(
                "word_economy",
                False,
                f"{beat.beat_id}: {wc} on-screen words — hard to read in {beat.duration_hint_sec}s",
                score=0.5,
                department="writers_room",
            ))

    # VO line length check
    for beat in script.beats:
        wc = len(beat.vo_line.split())
        if wc > 40:
            results.append(EvalResult(
                "vo_line_length",
                False,
                f"{beat.beat_id}: {wc} VO words (max 40 recommended)",
                score=0.5,
                department="writers_room",
            ))


    # CTA presence — final beat must be a call-to-action
    if script.beats:
        last_beat = script.beats[-1]
        has_cta = last_beat.beat_type == "cta"
        results.append(EvalResult(
            "cta_presence",
            has_cta,
            f"Final beat is '{last_beat.beat_type}'" if not has_cta else "Final beat is a CTA",
            department="writers_room",
        ))

    # Hook candidates exist
    if state.hook_selection:
        candidates = state.hook_selection.candidates
        if len(candidates) >= 3:
            viable = [c for c in candidates if c.score >= 0.5]
            results.append(EvalResult(
                "hook_candidates_viable",
                len(viable) >= 1,
                f"{len(viable)}/{len(candidates)} viable hooks (score ≥ 0.5)",
                department="writers_room",
            ))

    return results


# ── Visual Development ──

def _eval_visual_development(state: ProductionState) -> list[EvalResult]:
    results = []
    composed = state.composed_frames
    if not composed:
        return [EvalResult("composed_exists", False, "No ComposedFrames", department="visual_development")]

    script_beat_count = len(state.av_script.beats) if state.av_script else 0
    frame_beat_count = len(composed.frames)

    # Beat count match
    if script_beat_count:
        ok_match = frame_beat_count == script_beat_count
        results.append(EvalResult(
            "beat_count_match",
            ok_match,
            f"Script: {script_beat_count} beats, Frames: {frame_beat_count}",
            department="visual_development",
        ))

    # Headline word cap
    for frame in composed.frames:
        wc = len(frame.headline.split())
        if wc > 8:
            results.append(EvalResult(
                "headline_word_cap",
                False,
                f"{frame.beat_id}: {wc} headline words (max 8)",
                department="visual_development",
            ))

    # Safe zones
    unsafe = [f for f in composed.frames if not f.safe_margin_ok]
    results.append(EvalResult(
        "layout_safe_zones",
        len(unsafe) == 0,
        f"{len(unsafe)}/{frame_beat_count} beats fail safe zones" if unsafe else "All safe zones ok",
        score=1.0 - (len(unsafe) / max(frame_beat_count, 1)),
        department="visual_development",
    ))

    # Negative space ratio
    low_space = [f for f in composed.frames if f.negative_space_ratio < 0.2]
    if low_space:
        results.append(EvalResult(
            "negative_space",
            False,
            f"{len(low_space)} beats with negative_space_ratio < 0.2",
            department="visual_development",
        ))

    # Focal point variety
    focal_points = {f.focal_point for f in composed.frames if f.focal_point != "center"}
    center_only = all(f.focal_point == "center" for f in composed.frames)
    results.append(EvalResult(
        "focal_variety",
        not center_only,
        f"Focal zones used: {focal_points}" if focal_points else "All centered — AI slop detected",
        score=0.0 if center_only else 1.0,
        department="visual_development",
    ))

    return results


# ── Post-production ──

def _eval_postproduction(state: ProductionState) -> list[EvalResult]:
    results = []
    spec = state.video_spec
    if not spec:
        return [EvalResult("spec_exists", False, "No VideoSpec", department="postproduction")]

    # Min scenes
    ok_scenes = len(spec.scenes) >= 2
    results.append(EvalResult(
        "min_scenes",
        ok_scenes,
        f"{len(spec.scenes)} scenes (min 2)",
        department="postproduction",
    ))

    # All scenes have duration
    no_dur = [s.id for s in spec.scenes if s.duration_frames <= 0]
    results.append(EvalResult(
        "scene_durations",
        len(no_dur) == 0,
        f"Missing durations: {no_dur}" if no_dur else "All scenes have duration",
        department="postproduction",
    ))

    # Cut type variety
    cut_types = {s.cut_type for s in spec.scenes}
    if len(cut_types) <= 1 and len(spec.scenes) > 2:
        results.append(EvalResult(
            "cut_variety",
            False,
            f"Only 1 cut type used across {len(spec.scenes)} scenes — likely generic",
            department="postproduction",
        ))

    # Smash cut limit
    smash_count = sum(1 for s in spec.scenes if str(s.cut_type) == "smash_cut")
    if smash_count > 1:
        results.append(EvalResult(
            "smash_cut_limit",
            False,
            f"{smash_count} smash cuts (max 1 per 30s)",
            department="postproduction",
        ))

    # Dimensions
    ok_dims = spec.width == 1080 and spec.height == 1920
    results.append(EvalResult(
        "dimensions",
        ok_dims,
        f"{spec.width}x{spec.height} (expected 1080x1920)",
        department="postproduction",
    ))

    return results


# ── QC ──

def _eval_qc(state: ProductionState) -> list[EvalResult]:
    results = []
    spec = state.video_spec
    if not spec:
        return [EvalResult("spec_for_qc", False, "No VideoSpec for QC", department="qc")]

    # Theme tokens present
    theme = spec.theme
    required_tokens = ["primary", "secondary", "accent", "surface", "caption_highlight"]
    missing_tokens = [t for t in required_tokens if not getattr(theme, t, None)]
    results.append(EvalResult(
        "theme_tokens",
        len(missing_tokens) == 0,
        f"Missing tokens: {missing_tokens}" if missing_tokens else "All theme tokens present",
        department="qc",
    ))

    # Captions present
    has_captions = bool(spec.captions)
    results.append(EvalResult(
        "captions_present",
        has_captions,
        "Captions included" if has_captions else "No captions — may fail social platforms",
        score=0.5 if not has_captions else 1.0,
        department="qc",
    ))

    # Continuity check
    if state.continuity_bible and state.continuity_report:
        results.append(EvalResult(
            "continuity_pass",
            state.continuity_report.passes,
            f"Continuity: {state.continuity_report.severity}",
            department="qc",
        ))

    return results
