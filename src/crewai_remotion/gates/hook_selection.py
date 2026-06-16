"""Gate HookSelection: Producer picks hook before full script investment."""
from __future__ import annotations

from crewai_remotion.models.writers_room import HookCandidates, HookSelection


def gate_hook_selection(
    candidates: HookCandidates | HookSelection | None,
) -> tuple[bool, str]:
    """Validates that a hook has been selected before Copywriter runs."""
    if candidates is None:
        return False, "No hook candidates produced"

    # If it's a HookSelection with selected_id, check it's valid
    if isinstance(candidates, HookSelection):
        if not candidates.selected_id:
            return False, "No hook selected from candidates"
        if not candidates.candidates:
            return False, "HookSelection has no candidates list"
        selected_exists = any(
            c.id == candidates.selected_id for c in candidates.candidates
        )
        if not selected_exists:
            return False, f"Selected hook '{candidates.selected_id}' not in candidates list"
        return True, f"Hook selected: {candidates.selected_id}"

    # If it's HookCandidates, require at least 3 candidates scored > 0.5
    if isinstance(candidates, HookCandidates):
        if len(candidates.candidates) < 3:
            return False, f"Need at least 3 hook candidates, got {len(candidates.candidates)}"
        viable = [c for c in candidates.candidates if c.score >= 0.5]
        if len(viable) < 1:
            return False, "No hook candidates scored ≥ 0.5 — all would fail scroll-stop"
        return True, f"{len(candidates.candidates)} hook candidates, {len(viable)} viable"

    return False, "Unknown hook candidate type"
