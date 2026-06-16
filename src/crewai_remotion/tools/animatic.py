"""Animatic tool — gray-box timing proof before polish spend.

Renders a gray-box version of SocialVertical with scratch visuals, just
to validate pacing against RetentionBeatSheet. No motion polish, no color grade.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from crewai_remotion.config import get_settings


def render_animatic(
    run_output: Path,
    remotion_dir: Path | None = None,
) -> Path | None:
    """
    Render gray-box animatic from VideoSpec timing only.

    Uses a minimal props override: grayscale theme, no illustrations,
    scratch VO or silence. Returns path to animatic MP4 or None on failure.
    """
    settings = get_settings()
    remotion_dir = remotion_dir or (settings.root / "remotion")
    spec_path = run_output / "video_spec.json"

    if not spec_path.exists():
        return None

    # Build animatic spec — grayscale, no captions, scratch audio
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # Strip color and illustrations for gray-box render
    animatic_spec = {
        **spec,
        "theme": {
            **spec.get("theme", {}),
            "primary": "#888888",
            "secondary": "#555555",
            "accent": "#AAAAAA",
            "surface": "#222222",
            "caption_highlight": "#FFFFFF",
            "motion_style": "snappy",
            "texture": "none",
        },
        "captions": [],
    }
    # Remove illustration_ids
    for scene in animatic_spec.get("scenes", []):
        scene.pop("illustration_id", None)
        scene.pop("image_path", None)

    animatic_spec_path = run_output / "animatic_spec.json"
    animatic_spec_path.write_text(json.dumps(animatic_spec), encoding="utf-8")

    out_path = run_output / "animatic.mp4"
    try:
        subprocess.run(
            [
                "npx", "remotion", "render", "SocialVertical",
                str(out_path),
                f"--props={animatic_spec_path}",
                "--log=error",
            ],
            cwd=str(remotion_dir),
            check=True,
            timeout=120,
            capture_output=True,
        )
        return out_path if out_path.exists() else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
