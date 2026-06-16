from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from crewai_remotion.models.production_state import ProductionState


class CallSheet(BaseModel):
    run_id: str
    topic: str
    brand: str
    departments: list[str] = Field(default_factory=list)
    slates: dict[str, str] = Field(default_factory=dict)


class ProductionNotes(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    phase: str
    message: str
    handoff_ok: bool = True


def slate_version(phase: str, version: int = 1) -> str:
    return f"{phase}_v{version:02d}"


def write_call_sheet(state: ProductionState, path: Path) -> CallSheet:
    sheet = CallSheet(
        run_id=state.run_id,
        topic=state.effective_topic or state.topic,
        brand=state.brand_path,
        departments=[
            "development",
            "writers_room",
            "visual_development",
            "post_production",
            "qc",
        ],
        slates={
            "creative_brief": slate_version("brief"),
            "av_script": slate_version("script"),
            "composed_frames": slate_version("frames"),
            "video_spec": slate_version("spec"),
        },
    )
    path.write_text(json.dumps(sheet.model_dump(), indent=2), encoding="utf-8")
    return sheet


def log_note(state: ProductionState, phase: str, message: str, *, ok: bool = True) -> None:
    notes_path = state.run_output() / "production_notes.jsonl"
    note = ProductionNotes(phase=phase, message=message, handoff_ok=ok)
    with notes_path.open("a", encoding="utf-8") as f:
        f.write(note.model_dump_json() + "\n")
