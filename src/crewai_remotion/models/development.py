from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ── Topic Clarification ──

class ClarificationQuestion(BaseModel):
    id: str
    prompt: str
    choices: list[str] = Field(default_factory=list)
    allow_free_text: bool = True


class ClarificationQuestionnaire(BaseModel):
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    rationale: str = ""


class TopicClarification(BaseModel):
    raw_topic: str
    answers: dict[str, str] = Field(default_factory=dict)
    effective_topic: str = ""


class TopicAmbiguityResult(BaseModel):
    is_ambiguous: bool
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)


# ── Topic Researcher ──

class TopicResearchBrief(BaseModel):
    refined_angles: list[str] = Field(default_factory=list)
    key_facts: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


# ── Producer ──

class ComplexityBudget(BaseModel):
    max_beats: int = 5
    max_lottie_slots: int = 3
    max_motion_layers: int = 4
    max_words_vo: int = 120
    motion_intensity: Literal["low", "medium", "high"] = "medium"
    simplification_triggers: list[str] = Field(default_factory=list)
    approved: bool = True


class ProductionBrief(BaseModel):
    scope: str = ""
    constraints: list[str] = Field(default_factory=list)
    deliverable: str = "1080x1920 MP4"
    complexity_budget: ComplexityBudget = Field(default_factory=ComplexityBudget)


# ── Brand Strategist ──

class BrandAlignmentNotes(BaseModel):
    tone_rules: list[str] = Field(default_factory=list)
    vocabulary: list[str] = Field(default_factory=list)
    visual_do: list[str] = Field(default_factory=list)
    visual_dont: list[str] = Field(default_factory=list)


# ── Content Strategist ──

class RetentionAnchor(BaseModel):
    time_sec: float
    mechanism: str
    description: str


class RetentionBeatSheet(BaseModel):
    beats: list[str] = Field(default_factory=list)
    hook_window_sec: float = 3.0
    pattern_interrupts: list[str] = Field(default_factory=list)
    anchors: list[RetentionAnchor] = Field(default_factory=list)


class ContentStrategy(BaseModel):
    audience: str = ""
    platform: str = "TikTok/Reels"
    retention_mechanics: list[str] = Field(default_factory=list)


# ── Creative Director ──

class CreativeBrief(BaseModel):
    objective: str
    audience: str
    key_message: str
    tone_notes: str = ""
    cta: str = ""
    approved: bool = False
    locked: bool = False  # Once locked, ChangeOrder required for drift


class DepartmentKickoffMemo(BaseModel):
    vision: str = ""
    non_negotiables: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    do_not_list: list[str] = Field(default_factory=list)
    writers_room: str = ""
    visual_development: str = ""
    post_production: str = ""
