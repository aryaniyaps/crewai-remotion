"""Storyboard still-frame renderer.

Renders key composition stills from the VideoSpec via Remotion so the
vision gate can verify visual quality before the full render.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from rich.console import Console

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState

console = Console()

_STORYBOARD_FRAMES: list[tuple[str, float]] = [
    ("hook", 0.0),          # Opening / hook
    ("body_1", 0.25),       # First body point
    ("midpoint", 0.50),     # Mid-point
    ("body_2", 0.75),       # Second body point or stat
    ("cta", 0.90),          # Call-to-action
]


def render_storyboard(state: ProductionState) -> list[Path]:
    """Render key storyboard still frames from the VideoSpec.

    Returns list of PNG image paths.  Returns an empty list when
    remotion/npx is unavailable (non-blocking fallback).
    """
    settings = get_settings()
    run_output = state.run_output()
    remotion_dir = settings.root / settings.remotion_project_path

    # Ensure we have a VideoSpec on disk
    spec_path = run_output / "video_spec.json"
    if state.video_spec and not spec_path.exists():
        spec_path.write_text(
            json.dumps(state.video_spec.to_remotion_props(), indent=2),
            encoding="utf-8",
        )

    if not spec_path.exists():
        console.print("[yellow]storyboard: no video_spec.json — cannot render[/]")
        return []

    if not (remotion_dir / "package.json").exists():
        console.print("[yellow]storyboard: remotion project not found — skipping[/]")
        return []

    # Read spec for total frame count
    try:
        spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[yellow]storyboard: failed to read spec: {exc}[/]")
        return []

    total_frames = spec_data.get("duration_frames", 900)

    storyboard_dir = run_output / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    stills: list[Path] = []

    for label, fraction in _STORYBOARD_FRAMES:
        frame = max(0, min(int(total_frames * fraction), total_frames - 1))
        out_path = storyboard_dir / f"{label}_f{frame:04d}.png"

        console.print(f"  [dim]storyboard: rendering {label} @ frame {frame}[/]")

        try:
            subprocess.run(
                [
                    "npx", "remotion", "still", "SocialVertical",
                    str(out_path),
                    f"--props={spec_path}",
                    f"--frame={frame}",
                    "--log=error",
                ],
                cwd=str(remotion_dir),
                check=True,
                timeout=60,
                capture_output=True,
            )
            if out_path.exists():
                stills.append(out_path)
            else:
                console.print(
                    f"  [yellow]storyboard: {label} output not written[/]"
                )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            stderr = ""
            if hasattr(exc, "stderr") and exc.stderr:
                stderr = exc.stderr.decode(errors="replace")[:200]
            console.print(
                f"  [yellow]storyboard: {label} render failed: {stderr}[/]"
            )
        except FileNotFoundError:
            console.print(
                "[yellow]storyboard: npx/remotion not available — skipping all stills[/]"
            )
            break

    if stills:
        console.print(
            f"[green]storyboard: {len(stills)}/{len(_STORYBOARD_FRAMES)} stills captured[/]"
        )
    else:
        console.print(
            "[yellow]storyboard: no stills rendered (remotion may not be available)[/]"
        )

    return stills
