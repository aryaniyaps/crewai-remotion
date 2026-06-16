from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState


def render_video(state: ProductionState) -> Path:
    settings = get_settings()
    out = state.run_output()
    spec_path = out / "video_spec.json"
    if not spec_path.exists() and state.video_spec:
        spec_path.write_text(json.dumps(state.video_spec.to_remotion_props(), indent=2), encoding="utf-8")

    remotion_dir = settings.root / settings.remotion_project_path
    video_out = out / "video.mp4"

    if not (remotion_dir / "package.json").exists():
        return _placeholder_video(state, video_out)

    node_modules = remotion_dir / "node_modules"
    if not node_modules.exists():
        subprocess.run(["npm", "install"], cwd=remotion_dir, check=False, capture_output=True)
    props = json.loads(spec_path.read_text(encoding="utf-8"))
    props_file = (out / "render_props.json").resolve()
    props_file.write_text(json.dumps(props, indent=2), encoding="utf-8")
    video_out_abs = video_out.resolve()

    # Clean old public/runs to prevent bundle bloat (keep only current run)
    public_runs = remotion_dir / "public" / "runs"
    if public_runs.exists():
        for old_run in public_runs.iterdir():
            if old_run.is_dir() and old_run.name != state.run_id:
                shutil.rmtree(old_run, ignore_errors=True)

    cmd = [
        "npx",
        "remotion",
        "render",
        "SocialVertical",
        str(video_out_abs),
        "--props",
        str(props_file),
    ]
    result = subprocess.run(cmd, cwd=remotion_dir, capture_output=True, text=True)
    if result.returncode != 0 or not video_out.exists():
        (out / "render.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        return _placeholder_video(state, video_out)
    return video_out


def _placeholder_video(state: ProductionState, video_out: Path) -> Path:
    """Write deliverables bundle without ffmpeg if render unavailable."""
    bundle = {
        "status": "spec_ready",
        "message": "Video spec generated. Run `crewai-remotion render` after `npm install` in remotion/",
        "spec": str(state.run_output() / "video_spec.json"),
    }
    placeholder = state.run_output() / "video.placeholder.json"
    placeholder.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    if shutil.which("ffmpeg"):
        try:
            duration = max(int((state.video_spec.duration_frames if state.video_spec else 300) / 30), 1)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"color=c=0x1A1A2E:s=1080x1920:d={duration}",
                    "-f",
                    "lavfi",
                    "-i",
                    f"anullsrc=r=44100:cl=mono:d={duration}",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(video_out),
                ],
                check=True,
                capture_output=True,
            )
            return video_out
        except Exception:
            pass
    return placeholder
