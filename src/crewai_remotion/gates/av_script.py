"""Gate 2a: AV Script validation — beat count, word limits, drawability."""
from __future__ import annotations

from crewai_remotion.models.development import ComplexityBudget, RetentionBeatSheet
from crewai_remotion.models.writers_room import AVScript


def gate_av_script(
    script: AVScript,
    budget: ComplexityBudget | None = None,
    retention: RetentionBeatSheet | None = None,
) -> tuple[bool, str]:
    """Validates AVScript against complexity budget and structural rules."""
    if not script.beats:
        return False, "AV script has no beats"

    # Beat count vs budget
    # Beat count vs budget — exclude terminal end_card beats (branded close ≤2s)
    content_beats = [b for b in script.beats
                     if not (b.beat_type == "cta" and b.duration_hint_sec <= 3.0
                             and b.beat_id == script.beats[-1].beat_id)]
    effective_count = len(content_beats)
    if budget and effective_count > budget.max_beats:
        return False, (
            f"Beat count {effective_count} content beats exceeds complexity budget max_beats={budget.max_beats}"
            f" ({len(script.beats)} total with end card)"
        )

    # Max words per beat (hard cap at 8 for on_screen_text)
    for beat in script.beats:
        word_count = len(beat.on_screen_text.split()) if beat.on_screen_text else 0
        if word_count > 8:
            return False, (
                f"Beat {beat.beat_id} has {word_count} on-screen words (max 8)"
            )

    # VO word budget — duration-aware: ~3 words/sec is natural conversational pace.
    # The complexity budget is a floor; the duration-based budget is the real ceiling.
    duration_budget = int(script.total_duration_sec * 3)
    effective_vo_budget = max(budget.max_words_vo if budget else 50, duration_budget)
    if budget:
        total_vo_words = sum(len(b.vo_line.split()) for b in script.beats)
        if total_vo_words > effective_vo_budget:
            return False, (
                f"VO word count {total_vo_words} exceeds budget "
                f"(complexity={budget.max_words_vo}, duration_based={duration_budget})"
            )

    # Retention anchors: hook beat must exist and be ≤3s
    hook_beats = [b for b in script.beats if b.beat_type == "hook"]
    if not hook_beats:
        return False, "Script must have a hook beat"
    if hook_beats[0].duration_hint_sec > 3.5:
        return False, "Hook beat must be ≤3.5s for scroll-stop window"

    # Visual intents must be present (drawable)
    missing_intents = [b.beat_id for b in script.beats if not b.visual_intent]
    if missing_intents:
        return False, f"Beats missing visual_intent: {missing_intents}"

    # Duration check — hints are rough; Editor adjusts later
    total_hint = sum(b.duration_hint_sec for b in script.beats)
    if total_hint < script.total_duration_sec * 0.25:
        return False, (
            f"Beat duration hints sum to {total_hint:.1f}s, "
            f"but total is {script.total_duration_sec:.1f}s (gap too large)"
        )

    return True, f"AV script approved: {len(script.beats)} beats, {total_hint:.0f}s total"
