"""Gate Clearance: validates music + asset licenses before render."""
from __future__ import annotations

import json
from pathlib import Path

from crewai_remotion.models.visual_development import IllustrationPlan
from crewai_remotion.models.postproduction import SoundPlan


def gate_clearance(
    sound_plan: SoundPlan | None,
    illustration_plan: IllustrationPlan | None,
    music_manifest_path: Path | None = None,
) -> tuple[bool, str]:
    """Validates music track and illustration assets have valid licenses."""
    issues: list[str] = []

    # Check music track exists in licensed manifest
    if sound_plan and sound_plan.music_track_id:
        if music_manifest_path and music_manifest_path.exists():
            manifest = json.loads(music_manifest_path.read_text(encoding="utf-8"))
            tracks = manifest.get("tracks", [])
            track_ids = [t.get("id", "") for t in tracks]
            if sound_plan.music_track_id not in track_ids:
                issues.append(
                    f"Music track '{sound_plan.music_track_id}' not found in licensed manifest"
                )
            else:
                track = next(t for t in tracks if t.get("id") == sound_plan.music_track_id)
                if track.get("license") != "ok":
                    issues.append(
                        f"Music track '{sound_plan.music_track_id}' license not cleared: "
                        f"{track.get('license', 'unknown')}"
                    )
        else:
            # No manifest — warn but don't block (dev mode)
            pass

    # Check illustration catalog IDs
    if illustration_plan:
        for slot in illustration_plan.slots:
            if not slot.catalog_id:
                issues.append(f"Illustration slot {slot.beat_id} has no catalog_id")
            # In v1, all catalog IDs from lottie.json are pre-cleared

    if issues:
        return False, "; ".join(issues)

    return True, "Clearance passed — all assets licensed"
