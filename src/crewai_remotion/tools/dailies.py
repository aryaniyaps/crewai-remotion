"""Dailies review — extract key frames from rendered MP4 and compare against ComposedFrames.

Catches implementation drift (Mograph TD placed text wrong) that QC on spec alone misses.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from crewai_remotion.models.production_state import ProductionState, DailiesReport


def _expected_rendered_frames(state: ProductionState) -> int:
    spec = state.video_spec
    if not spec:
        return 0
    audio_frames = int(spec.audio.duration_sec * spec.fps) if spec.audio.duration_sec else spec.duration_frames
    return max(1, min(spec.duration_frames, audio_frames))


def _probe_video_frames(video_path: Path) -> int | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=nb_frames",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    return int(value) if value.isdigit() else None


def run_dailies(
    state: ProductionState,
    video_path: Path | None = None,
) -> DailiesReport:
    """
    Extract 3 key frames from rendered MP4 and compare against ComposedFrames zones.

    In v1, this is a heuristic check — pixel-perfect SSIM comparison requires
    ffmpeg + imagemagick which are heavy deps. Instead, we verify:
    1. MP4 file exists and has non-zero size
    2. Frame count matches spec
    3. Key frame positions exist in ComposedFrames

    Returns DailiesReport with pass/fail and drift score.
    """
    if video_path is None:
        run_dir = state.run_output()
        video_path = run_dir / "video.mp4"

    issues: list[dict] = []

    # Check 1: file exists
    if not video_path or not video_path.exists():
        return DailiesReport(
            passes=False,
            drift_score=0.0,
            frame_comparisons=[{"error": "Video file not found"}],
        )

    file_size = video_path.stat().st_size
    if file_size < 1024:
        issues.append({"error": f"Video file too small: {file_size} bytes"})

    # Check 2: frame count from rendered media vs expected composition duration.
    if state.video_spec:
        expected_frames = _expected_rendered_frames(state)
        actual_frames = _probe_video_frames(video_path)
        if actual_frames is None:
            issues.append({"warning": "Could not probe rendered frame count with ffprobe"})
            drift = 0.0
        else:
            drift = abs(actual_frames - expected_frames) / max(expected_frames, 1)
            if drift > 0.08:
                issues.append({
                    "error": f"Rendered frame count drift: {drift:.1%}",
                    "expected_frames": expected_frames,
                    "actual_frames": actual_frames,
                })
    else:
        drift = 0.0

    # Check 3: ComposedFrames zones have corresponding beats
    if state.composed_frames and state.video_spec:
        composed_ids = {f.beat_id for f in state.composed_frames.frames}
        spec_ids = {s.id for s in state.video_spec.scenes}
        missing = composed_ids - spec_ids
        extra = spec_ids - composed_ids
        if missing:
            issues.append({"error": f"ComposedFrames beats missing from spec: {missing}"})
        if extra:
            issues.append({"warning": f"Spec beats not in ComposedFrames: {extra}"})

    # Check 4: continuity bible vs spec headlines
    if state.continuity_bible and state.video_spec:
        bible_texts = set(state.continuity_bible.on_screen_text)
        spec_headlines = {s.headline for s in state.video_spec.scenes}
        # Semantic drift — headlines that don't match any bible text
        orphan = spec_headlines - bible_texts
        if orphan and len(orphan) > len(spec_headlines) * 0.5:
            issues.append({
                "error": f"Major headline drift: {len(orphan)} headlines not in continuity bible",
                "orphan_samples": list(orphan)[:3],
            })

    dailies_path = state.run_output() / "dailies.json"
    passes = len(issues) == 0

    report = DailiesReport(
        passes=passes,
        drift_score=drift if 'drift' in dir() else 0.0,
        frame_comparisons=issues if issues else [{"status": "ok"}],
    )

    # Write report for trace
    dailies_path.write_text(json.dumps({
        "passes": report.passes,
        "drift_score": report.drift_score,
        "issues": issues,
        "video_path": str(video_path),
        "file_size_bytes": file_size,
    }, indent=2), encoding="utf-8")

    return report
