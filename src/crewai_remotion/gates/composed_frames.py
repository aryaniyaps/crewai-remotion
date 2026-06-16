from crewai_remotion.models.visual_development import ComposedFrames


def gate_composed_frames(frames: ComposedFrames | None) -> tuple[bool, str]:
    if not frames or not frames.frames:
        return False, "No composed frames"
    for f in frames.frames:
        if len(f.headline.split()) > 12:
            return False, f"Headline too long on beat {f.beat_id}"
    return True, "Composed frames approved"
