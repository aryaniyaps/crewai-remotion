from __future__ import annotations

from pathlib import Path

from rich.console import Console

from crewai_remotion.errors import ProductionError
from crewai_remotion.models.production_state import ProductionState

console = Console()


def validate_run(state: ProductionState, *, expect_video: bool) -> None:
    out = state.run_output()
    run_dir = str(out)

    spec = out / "video_spec.json"
    if not spec.exists():
        raise ProductionError(
            "video_spec.json was not written",
            phase="delivery",
            hint="Inspect production_notes.jsonl in the run folder for the failing phase.",
            run_dir=run_dir,
        )

    voice = out / "voice.wav"
    if voice.exists() and voice.stat().st_size < 8_000:
        console.print(
            "[yellow]Warning:[/yellow] voice.wav is very small — Piper TTS may have failed. "
            f"See {out / 'tts_error.txt'}"
        )

    if not expect_video:
        return

    placeholder = out / "video.placeholder.json"
    if placeholder.exists():
        raise ProductionError(
            "Remotion render did not produce a video",
            phase="render",
            hint="Run: cd remotion && npm install && npx remotion render. "
            "Or render later with: crewai-remotion render --spec output/<run-id>/video_spec.json",
            run_dir=run_dir,
        )

    video = out / "video.mp4"
    if not video.exists():
        raise ProductionError(
            "video.mp4 is missing after render",
            phase="render",
            hint=f"Check {out / 'render.log'} if present.",
            run_dir=run_dir,
        )

    if video.stat().st_size < 10_000:
        raise ProductionError(
            "video.mp4 exists but looks empty or corrupt",
            phase="render",
            hint=f"Check {out / 'render.log'} and re-run render for this spec.",
            run_dir=run_dir,
        )

    render_log = out / "render.log"
    if render_log.exists():
        log_text = render_log.read_text(encoding="utf-8", errors="replace")
        if "Error" in log_text or "error" in log_text.lower():
            console.print(
                f"[yellow]Warning:[/yellow] render.log contains errors — verify {video} looks correct."
            )
