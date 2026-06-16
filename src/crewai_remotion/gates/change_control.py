"""Gate ChangeControl: blocks silent creative brief drift post-lock."""
from __future__ import annotations

from crewai_remotion.models.cinematic_cuts import ChangeOrder
from crewai_remotion.models.development import CreativeBrief


def gate_change_control(
    original: CreativeBrief | None,
    current: CreativeBrief | None,
    change_orders: list[ChangeOrder] | None = None,
) -> tuple[bool, str]:
    """
    After creative brief is locked, any agent output that contradicts
    the locked brief must have an approved ChangeOrder.
    """
    if original is None or current is None:
        return True, "No brief to compare — skipping change control"
    if not original.locked:
        return True, "Brief not locked — changes allowed"

    drift_fields: list[str] = []

    if current.key_message and current.key_message != original.key_message:
        drift_fields.append("key_message")
    if current.audience and current.audience != original.audience:
        drift_fields.append("audience")
    if current.objective and current.objective != original.objective:
        drift_fields.append("objective")
    if current.tone_notes and current.tone_notes != original.tone_notes:
        drift_fields.append("tone_notes")
    if current.cta and current.cta != original.cta:
        drift_fields.append("cta")

    if not drift_fields:
        return True, "No brief drift detected"

    # Check if any approved change order covers these fields
    approved_orders = [co for co in (change_orders or []) if co.approved]
    covered = set()
    for co in approved_orders:
        covered.add(co.field_changed)

    unapproved = [f for f in drift_fields if f not in covered]
    if unapproved:
        return False, (
            f"Creative brief drift on: {unapproved}. "
            f"Requires approved ChangeOrder from Producer."
        )

    return True, f"Brief changes approved via ChangeOrders for: {drift_fields}"


def lock_brief(brief: CreativeBrief) -> CreativeBrief:
    """Lock the creative brief — enables change control."""
    brief.locked = True
    return brief
