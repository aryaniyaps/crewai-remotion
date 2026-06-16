"""Smoke stills — pre-render frame captures to fail fast.

Before full remotion render, capture stills at frames 0, mid, end.
If any fail, block full render and route to Mograph TD.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from crewai_remotion.config import get_settings


def smoke_test_stills(
    run_output: Path,
    remotion_dir: Path | None = None,
) -> tuple[bool, str, list[Path]]:
    """
    Render test stills at key frames.

    Returns (passed, error_message, [still_paths]).
    """
    settings = get_settings()
    remotion_dir = remotion_dir or (settings.root / "remotion")
    spec_path = run_output / "video_spec.json"

    if not spec_path.exists():
        return False, f"VideoSpec not found: {spec_path}", []

    # Read spec to determine frame range
    import json
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return False, f"Failed to read spec: {exc}", []

    fps = int(spec.get("fps", 30) or 30)
    spec_frames = int(spec.get("duration_frames", 300) or 300)
    audio_duration = (spec.get("audio") or {}).get("duration_sec")
    audio_frames = int(float(audio_duration) * fps) if audio_duration else spec_frames
    # calculateMetadata trims composition duration to audio duration; avoid probing
    # frames beyond the rendered composition.
    total_frames = max(1, min(spec_frames, audio_frames))
    mid_frame = total_frames // 2
    end_frame = max(0, total_frames - 1)

    stills_dir = run_output / "stills"
    stills_dir.mkdir(parents=True, exist_ok=True)

    test_frames = {
        "frame_0": 0,
        "frame_mid": mid_frame,
        "frame_end": end_frame,
    }

    failures: list[str] = []
    stills: list[Path] = []

    for name, frame in test_frames.items():
        out_path = stills_dir / f"{name}.png"
        try:
            subprocess.run(
                [
                    "npx", "remotion", "still", "SocialVertical",
                    str(out_path.resolve()),
                    f"--props={spec_path.resolve()}",
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
                failures.append(f"{name}: output not written")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            stderr = ""
            if hasattr(exc, "stderr") and exc.stderr:
                stderr = exc.stderr.decode(errors="replace")[:200]
            failures.append(f"{name}: {stderr}")
        except FileNotFoundError:
            failures.append(f"{name}: remotion/npx not found")

    if failures:
        return False, f"Smoke test failed: {'; '.join(failures)}", stills

    return True, f"Smoke test passed: {len(stills)} stills captured", stills
