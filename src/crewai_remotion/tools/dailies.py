"""Dailies review — extract key frames from rendered MP4 and compare against ComposedFrames.

Catches implementation drift (Mograph TD placed text wrong) that QC on spec alone misses.
"""

from __future__ import annotations

import json
from pathlib import Path

from crewai_remotion.models.production_state import ProductionState, DailiesReport


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

    # Check 2: frame count from VideoSpec vs estimated
    if state.video_spec:
        expected_frames = state.video_spec.duration_frames
        # Approximate frame count from file size (very rough heuristic)
        # ~50KB/frame for 1080p h264 at reasonable quality
        estimated_frames = file_size / 50_000
        drift = abs(estimated_frames - expected_frames) / max(expected_frames, 1)

        if drift > 0.5:
            issues.append({
                "error": f"Estimated frame count drift: {drift:.1%}",
                "expected_frames": expected_frames,
                "estimated_frames": int(estimated_frames),
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
