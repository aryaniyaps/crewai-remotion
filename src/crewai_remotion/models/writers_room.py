from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Hook Strategist ──

class HookCandidate(BaseModel):
    id: str
    text: str
    pattern: Literal["question", "contrarian", "stat-shock", "story", "how-to"] = "question"
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    scroll_stop_rationale: str = ""


class HookCandidates(BaseModel):
    candidates: list[HookCandidate] = Field(default_factory=list)


class HookSelection(BaseModel):
    candidates: list[HookCandidate] = Field(default_factory=list)
    selected_id: str = ""
    rationale: str = ""


# ── Copywriter ──

class AVBeat(BaseModel):
    beat_id: str
    beat_type: Literal["hook", "point", "stat", "quote", "cta", "rehook"] = "point"
    vo_line: str
    on_screen_text: str = ""
    visual_intent: str = ""   # what the viewer should SEE, not layout
    duration_hint_sec: float = 4.0


class AVScript(BaseModel):
    title: str
    hook: str
    beats: list[AVBeat] = Field(default_factory=list)
    cta: str = ""
    total_duration_sec: float = 30.0
    approved: bool = False


# ── Script Supervisor ──

class ContinuityBible(BaseModel):
    canonical_vo_lines: list[str] = Field(default_factory=list)
    on_screen_text: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    cta: str = ""
    version: int = 1


class ContinuityReport(BaseModel):
    """Script Supervisor output — catches drift between script and frames."""
    passes: bool = False
    issues: list[dict[str, str]] | None = Field(default=None)
    severity: str = "none"
    responsible_role: str = ""
