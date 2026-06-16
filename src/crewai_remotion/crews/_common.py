from __future__ import annotations
from pathlib import Path


def _load_reference(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "references" / name
    return path.read_text(encoding="utf-8") if path.exists() else ""
