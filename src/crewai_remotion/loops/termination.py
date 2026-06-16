"""Termination goals — verifiable stop conditions for production runs.

The Flow blocks "done" until PRODUCTION_GOAL is satisfied — not until an agent claims done.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProductionGoal:
    all_gates_pass: bool = True
    component_eval_min: float = 0.75       # per-phase floor
    e2e_ship_score_min: float = 0.80       # FlywheelCoach aggregate
    render_exit_code: int = 0
    revision_count_max: int = 2
    required_artifacts: list[str] = field(default_factory=lambda: [
        "creative_brief",
        "av_script",
        "composed_frames",
        "edit_decisions",
        "video_spec",
    ])

    def is_satisfied(
        self,
        *,
        gates_passed: bool,
        eval_scores: dict[str, float],
        render_exit: int,
        revision_count: int,
    ) -> tuple[bool, str]:
        """Check if production goals are met."""
        if not gates_passed:
            return False, "Not all gates passed"
        if revision_count > self.revision_count_max:
            return False, f"Revision count {revision_count} exceeds max {self.revision_count_max}"
        if render_exit != self.render_exit_code:
            return False, f"Render exit code {render_exit}, expected {self.render_exit_code}"

        failing_evals = {k: v for k, v in eval_scores.items() if v < self.component_eval_min}
        if failing_evals:
            return False, f"Eval scores below {self.component_eval_min}: {failing_evals}"

        return True, "All production goals met"


PRODUCTION_GOAL = ProductionGoal()
