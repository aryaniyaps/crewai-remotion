from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.models.video_spec import VideoSpec


def gate_qc(state: ProductionState, spec: VideoSpec | None) -> tuple[bool, str, str | None]:
    """Returns (pass, message, revision_department)."""
    if not spec or not spec.scenes:
        return False, "Missing video spec", "visual_development"
    if state.revision_count >= 2:
        return True, "QC pass with contingency simplification", None
    if len(spec.scenes) < 2:
        return False, "Too few scenes", "writers_room"
    return True, "QC passed", None
