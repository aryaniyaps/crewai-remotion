from __future__ import annotations

import base64
import json
from pathlib import Path

import cv2
from openai import OpenAI
from rich.console import Console

from crewai_remotion.config import get_settings
from crewai_remotion.gates.coordinator import log_note
from crewai_remotion.models.production_state import ProductionState

console = Console()

_CRITIQUE_PROMPT = (
    "You are a visual design critic for short-form social videos (TikTok/Reels style). "
    "Analyze this frame from a vertical video and critique: "
    "1) Text readability and placement "
    "2) Color contrast and harmony "
    "3) Visual hierarchy "
    "4) Image quality and relevance "
    "5) Overall appeal. "
    "Be specific and actionable. Suggest concrete improvements."
)

_VISION_MODEL = "gpt-4o-mini"


def capture_frame(video_path: str | Path, frame_number: int, output_path: str | Path) -> Path:
    """Extract a single frame from a video and save it as a JPEG image."""
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, frame = cap.read()
        if not ok:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            raise RuntimeError(
                f"Failed to read frame {frame_number} from {video_path} (total frames: {total_frames})"
            )
        cv2.imwrite(str(output_path), frame)
    finally:
        cap.release()

    return output_path


def critique_frame(image_path: str | Path, topic: str = "") -> str:
    """Send a frame image to gpt-4o for visual design critique."""
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for visual QA critique")

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Frame image not found: {image_path}")

    image_bytes = image_path.read_bytes()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    mime = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _CRITIQUE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64_image}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ],
        max_tokens=1024,
    )

    critique = response.choices[0].message.content or ""
    return critique.strip()


def run_visual_qa(state: ProductionState) -> dict:
    """Capture 3 frames from the rendered video and run vision LLM critique.

    Returns a dict with keys: critiques (list of frame critiques), revision_suggestions (str).
    Does not block the pipeline — stores results and returns them.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        console.print("[dim]Visual QA skipped: no OPENAI_API_KEY set[/dim]")
        return {"critiques": [], "revision_suggestions": ""}

    if state.delivery is None or not state.delivery.video_path:
        console.print("[dim]Visual QA skipped: no rendered video in delivery manifest[/dim]")
        return {"critiques": [], "revision_suggestions": ""}

    out_dir = state.run_output()
    video_path = out_dir / state.delivery.video_path
    if not video_path.exists():
        console.print(f"[dim]Visual QA skipped: video not found at {video_path}[/dim]")
        return {"critiques": [], "revision_suggestions": ""}

    # Determine frame positions: 25%, 50%, 75% of total
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        console.print(f"[dim]Visual QA skipped: cannot open {video_path}[/dim]")
        return {"critiques": [], "revision_suggestions": ""}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if total_frames < 3:
        console.print(f"[dim]Visual QA skipped: video has only {total_frames} frames[/dim]")
        return {"critiques": [], "revision_suggestions": ""}

    frame_positions = [
        max(0, total_frames // 4),       # 25%
        total_frames // 2,                # 50%
        max(0, (total_frames * 3) // 4),  # 75%
    ]

    qa_dir = out_dir / "qa_frames"
    qa_dir.mkdir(exist_ok=True)

    topic = state.effective_topic or state.topic
    critiques: list[dict] = []

    for i, frame_num in enumerate(frame_positions):
        frame_path = qa_dir / f"frame_{i + 1:02d}_f{frame_num:05d}.jpg"
        try:
            capture_frame(video_path, frame_num, frame_path)
            critique_text = critique_frame(frame_path, topic)

            critique_entry = {
                "frame_number": frame_num,
                "frame_path": str(frame_path.relative_to(out_dir)),
                "critique": critique_text,
            }
            critiques.append(critique_entry)

            console.print(
                f"[green]Visual QA[/green] frame {i + 1}/3 (f#{frame_num}): critique received"
            )
        except Exception as exc:
            console.print(f"[yellow]Visual QA[/yellow] frame {i + 1}/3 failed: {exc}")
            critiques.append({
                "frame_number": frame_num,
                "frame_path": "",
                "critique": f"ERROR: {exc}",
            })

    # Compile revision suggestions from all critiques
    if critiques:
        synthesis_parts = []
        for c in critiques:
            if c["critique"] and not c["critique"].startswith("ERROR:"):
                synthesis_parts.append(f"Frame {c['frame_number']}:\n{c['critique']}")
        revision_suggestions = "\n\n---\n\n".join(synthesis_parts)
    else:
        revision_suggestions = ""

    # Persist QA report
    report = {
        "topic": topic,
        "total_frames": total_frames,
        "sampled_frames": frame_positions,
        "critiques": critiques,
        "revision_suggestions": revision_suggestions,
    }
    report_path = qa_dir / "visual_qa_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    log_note(state, "visual_qa", f"Critiqued {len(critiques)} frames; report saved")

    return {"critiques": critiques, "revision_suggestions": revision_suggestions}
