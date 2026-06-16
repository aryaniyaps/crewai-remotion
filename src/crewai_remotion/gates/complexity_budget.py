"""Gate ComplexityBudget: validates downstream artifacts against Producer's budget."""
from __future__ import annotations

from crewai_remotion.models.development import ComplexityBudget
from crewai_remotion.models.visual_development import ComposedFrames, IllustrationPlan
from crewai_remotion.models.writers_room import AVScript


def gate_complexity_budget(
    budget: ComplexityBudget | None,
    script: AVScript | None = None,
    composed: ComposedFrames | None = None,
    illustration: IllustrationPlan | None = None,
) -> tuple[bool, str]:
    """
    Every downstream artifact validated against the complexity budget.
    Compositor cannot add beats; Motion Designer cannot exceed intensity cap.
    """
    if budget is None or not budget.approved:
        return True, "No budget set — skipping validation"

    issues: list[str] = []

    # Beat count
    if script:
        if len(script.beats) > budget.max_beats:
            issues.append(
                f"Script beat count {len(script.beats)} exceeds budget max {budget.max_beats}"
            )

    # ComposedFrames beat count
    if composed:
        if len(composed.frames) > budget.max_beats:
            issues.append(
                f"ComposedFrames beat count {len(composed.frames)} exceeds budget max {budget.max_beats}"
            )

    # Lottie / illustration slots
    if illustration:
        lottie_slots = len([s for s in illustration.slots if s.asset_type == "lottie"])
        if lottie_slots > budget.max_lottie_slots:
            issues.append(
                f"Lottie slots {lottie_slots} exceeds budget max {budget.max_lottie_slots}"
            )

    # Motion layers check — infer from composed frames
    if composed:
        max_layers = max(
            (1 + (1 if f.illustration_id else 0) + (1 if f.subhead else 0))
            for f in composed.frames
        )
        if max_layers > budget.max_motion_layers:
            issues.append(
                f"Motion layers {max_layers} exceeds budget max {budget.max_motion_layers}"
            )

    if issues:
        return False, "; ".join(issues)

    return True, f"Within complexity budget: {budget.max_beats} beats, {budget.max_lottie_slots} lottie slots"
