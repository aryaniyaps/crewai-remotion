"""Gate StyleFrames: CD approves look before full visual build."""
from __future__ import annotations

from crewai_remotion.models.visual_development import StyleFrameSpecs


def gate_style_frames(specs: StyleFrameSpecs) -> tuple[bool, str]:
    """Blocks Production Designer → Compositor chain until CD approves style frames."""
    if not specs.frames:
        return False, "No style frames submitted"

    if len(specs.frames) < 2:
        return False, "Need at least 2 style frames (hook + mid beat)"

    # Hook frame must be approved
    hook_frame = next((f for f in specs.frames if f.beat_id and "hook" in f.beat_id.lower()), None)
    if hook_frame is None:
        # Fall back to first frame as hook representative
        hook_frame = specs.frames[0]

    if not hook_frame.approved:
        return False, f"Style frame {hook_frame.beat_id} not approved by Creative Director"

    # At least one mid-video frame must be approved
    mid_approved = any(
        f.approved and f.beat_id != hook_frame.beat_id
        for f in specs.frames
    )
    if not mid_approved:
        return False, "No mid-video style frame approved"

    return True, f"Style frames approved: {len(specs.frames)} frames, CD sign-off on {hook_frame.beat_id}"
