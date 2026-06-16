from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from crewai_remotion.models.cinematic_cuts import CutType


# ── Reference Librarian ──

class MoodReference(BaseModel):
    tag: str
    rationale: str
    apply_to_beats: list[str] = Field(default_factory=list)


class MoodBoard(BaseModel):
    references: list[MoodReference] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


# ── Art Director ──

class StyleBible(BaseModel):
    mood_keywords: list[str] = Field(default_factory=list)
    reference_urls: list[str] = Field(default_factory=list)
    do_list: list[str] = Field(default_factory=list)
    dont_list: list[str] = Field(default_factory=list)
    color_emphasis: str = "primary"
    texture: Literal["none", "grain", "paper"] = "grain"


class StyleFrameSpec(BaseModel):
    beat_id: str
    mood: str
    color_emphasis: str = "primary"
    layout_notes: str = ""
    font_tier: str = "display"
    illustration_slot: str = ""
    background_variant: str = "primary"
    approved: bool = False


class StyleFrameSpecs(BaseModel):
    frames: list[StyleFrameSpec] = Field(default_factory=list)


class StyleFrameApproval(BaseModel):
    approved: bool = False
    reviewer: str = "Creative Director"
    notes: str = ""


# ── Production Designer ──

class PerBeatEnvironment(BaseModel):
    beat_id: str
    background_type: str = "gradient_mesh"
    depth_layers: int = 2
    gradient_direction: str = "top_to_bottom"
    atmospheric_density: float = Field(default=0.3, ge=0.0, le=1.0)


class EnvironmentPlan(BaseModel):
    beats: list[PerBeatEnvironment] = Field(default_factory=list)
    background_style: str = "gradient_mesh"
    depth_layers: int = 2
    texture: Literal["none", "grain", "paper"] = "grain"


# ── Typography Director ──

class PerBeatTypeSpec(BaseModel):
    beat_id: str
    tier: Literal["display", "headline", "body", "caption"] = "headline"
    weight_contrast: int = 200   # diff between heading and body weight
    alignment: Literal["left", "center", "right"] = "left"
    max_lines: int = 2
    emphasis_words: list[str] = Field(default_factory=list)


class TypeSpec(BaseModel):
    beats: list[PerBeatTypeSpec] = Field(default_factory=list)
    headline_tier: str = "display"
    body_tier: str = "body"
    max_words_headline: int = 8
    contrast_ratio_min: float = 4.5


# ── Illustrator ──

class IllustrationSlot(BaseModel):
    beat_id: str
    asset_type: Literal["lottie", "svg", "shape", "photo"] = "lottie"
    catalog_id: str
    placement_zone: str = "tr"   # tl, tr, ml, mr, bl, br, center
    scale_tier: Literal["sm", "md", "lg"] = "md"


class IllustrationPlan(BaseModel):
    slots: list[IllustrationSlot] = Field(default_factory=list)


# ── Storyboard Artist ──


class StoryboardFrame(BaseModel):
    """Per-frame storyboard data for visual verification."""
    beat_id: str
    frame_index: int = 0  # 0-based index within the composition
    description: str = ""  # what should be visible
    composition_notes: str = ""
    approved: bool = False


class StoryboardFrameSet(BaseModel):
    """Collection of storyboard frames keyed by label (hook, body, cta)."""
    frames: dict[str, StoryboardFrame] = Field(default_factory=dict)
    pacing_notes: str = ""
    total_beats: int = 0


class RoughStoryboardBeat(BaseModel):
    beat_id: str
    action: str
    camera_notes: str = ""
    cut_type_intent: CutType = CutType.HARD_CUT
    audio_sync_hint: str = ""
    frame_index: int = 0
    composition_notes: str = ""
    approved: bool = False


class RoughStoryboard(BaseModel):
    beats: list[RoughStoryboardBeat] = Field(default_factory=list)
    pacing_notes: str = ""
    total_beats: int = 0

# ── Compositor ──

class ComposedFrame(BaseModel):
    beat_id: str
    scene_type: str  # HookBeat | PointBeat | StatBeat | QuoteBeat | CTABeat
    headline: str
    subhead: str = ""
    # Layout
    focal_point: str = "center"   # tl, tr, ml, mr, bl, br, center
    headline_zone: str = "tl"     # tl, tr, ml, mr, bl, br, tc, bc
    illustration_zone: str | None = None
    logo_zone: str | None = None
    negative_space_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    balance_notes: str = ""
    safe_margin_ok: bool = True
    # Visual
    illustration_id: str | None = None
    image_path: str | None = None
    background_variant: str = "primary"
    layout: str = "left_stack"
    motion_intent: str = "enter_up"


class ComposedFrames(BaseModel):
    frames: list[ComposedFrame] = Field(default_factory=list)
    approved: bool = False
    beat_count: int = 0
    safe_zones_ok: bool = False


# ── Creative Review ──

class CreativeReviewNotes(BaseModel):
    """Creative Director's table-read notes."""
    brief_execution_score: float = Field(default=0.0, ge=0.0, le=1.0)
    prioritized_issues: list[str] = Field(default_factory=list)
    approved: bool = False


class ArtReviewNotes(BaseModel):
    visual_cohesion_score: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class LayoutReviewNotes(BaseModel):
    readability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


# ── Clearance ──

class FeasibilityReport(BaseModel):
    """Pipeline TD checks ComposedFrames against Remotion capabilities."""
    passes: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class BrandComplianceReport(BaseModel):
    """Brand Guardian adversarial check against brand YAML."""
    passes: bool = False
    violations: list[str] = Field(default_factory=list)
    severity: str = "none"


# ── Revision Notes ──

class RevisionNotes(BaseModel):
    beat_id: str
    department: str
    issue: str
    requested_fix: str
    severity: Literal["block", "warn"] = "block"
