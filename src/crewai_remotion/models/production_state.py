from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import (
    BrandAlignmentNotes,
    ClarificationQuestionnaire,
    ComplexityBudget,
    ContentStrategy,
    CreativeBrief,
    DepartmentKickoffMemo,
    ProductionBrief,
    RetentionBeatSheet,
    TopicAmbiguityResult,
    TopicClarification,
    TopicResearchBrief,
)
from crewai_remotion.models.postproduction import (
    CaptionStyle,
    ColorPlan,
    DeliveryManifest,
    MotionPlan,
    PostBrief,
    SoundPlan,
    VODirection,
)
from crewai_remotion.models.video_spec import VideoSpec
from crewai_remotion.models.visual_development import (
    ArtReviewNotes,
    BrandComplianceReport,
    ComposedFrames,
    CreativeReviewNotes,
    EnvironmentPlan,
    FeasibilityReport,
    IllustrationPlan,
    LayoutReviewNotes,
    MoodBoard,
    RevisionNotes,
    RoughStoryboard,
    StyleBible,
    StyleFrameApproval,
    StyleFrameSpecs,
    TypeSpec,
)
from crewai_remotion.models.writers_room import (
    AVScript,
    ContinuityBible,
    ContinuityReport,
    HookCandidates,
    HookSelection,
)
from crewai_remotion.models.asset_research import AssetResearchBrief, SceneImageManifest
from crewai_remotion.models.cinematic_cuts import (
    ChangeOrder,
    EditDecisionList,
    PictureLockCertificate,
)
from crewai_remotion.config import get_settings


def _new_run_id() -> str:
    return uuid.uuid4().hex[:12]


class EvalResult(BaseModel):
    metric_id: str = ""
    score: float = 0.0
    passed: bool = False
    message: str = ""


class RunScorecard(BaseModel):
    overall_score: float = 0.0
    failure_modes: list[str] = Field(default_factory=list)
    department_weaknesses: dict[str, float] = Field(default_factory=dict)
    distill_candidates: list[str] = Field(default_factory=list)


class QCVerdict(BaseModel):
    passes: bool = False
    issues: list[dict[str, str]] | None = Field(default=None)
    responsible_dept: str = ""


class DailiesReport(BaseModel):
    passes: bool = False
    drift_score: float = 0.0
    frame_comparisons: list[dict[str, Any]] = Field(default_factory=list)


class ProductionState(BaseModel):
    id: str = Field(default_factory=_new_run_id)
    run_id: str = ""
    topic: str = ""
    effective_topic: str = ""
    topic_ambiguity_score: float | None = None
    duration_sec: float = 30.0
    brand_path: str = ""
    brand: BrandProfile | None = None
    output_dir: str = ""
    strict_qa_override: bool = False


    # ── Topic ──
    questionnaire: ClarificationQuestionnaire | None = None
    topic_ambiguity: TopicAmbiguityResult | None = None
    topic_clarification: TopicClarification | None = None
    topic_research: TopicResearchBrief | None = None

    # ── Development ──
    production_brief: ProductionBrief | None = None
    complexity_budget: ComplexityBudget | None = None
    brand_alignment: BrandAlignmentNotes | None = None
    content_strategy: ContentStrategy | None = None
    retention_beat_sheet: RetentionBeatSheet | None = None
    creative_brief: CreativeBrief | None = None
    kickoff_memo: DepartmentKickoffMemo | None = None
    production_notes: list[str] = Field(default_factory=list)
    change_orders: list[ChangeOrder] = Field(default_factory=list)
    artifact_versions: dict[str, int] = Field(default_factory=dict)

    # ── Writers Room ──
    hook_candidates: HookCandidates | None = None
    hook_selection: HookSelection | None = None
    av_script: AVScript | None = None
    continuity_bible: ContinuityBible | None = None

    # ── Visual Development ──
    mood_board: MoodBoard | None = None
    style_bible: StyleBible | None = None
    style_frame_specs: StyleFrameSpecs | None = None
    style_frame_approval: StyleFrameApproval | None = None
    environment_plan: EnvironmentPlan | None = None
    type_spec: TypeSpec | None = None
    illustration_plan: IllustrationPlan | None = None
    rough_storyboard: RoughStoryboard | None = None
    composed_frames: ComposedFrames | None = None
    asset_research: AssetResearchBrief | None = None
    scene_images: SceneImageManifest | None = None

    # ── Creative Review + Clearance ──
    creative_review_notes: CreativeReviewNotes | None = None
    art_review_notes: ArtReviewNotes | None = None
    layout_review_notes: LayoutReviewNotes | None = None
    feasibility_report: FeasibilityReport | None = None
    brand_compliance: BrandComplianceReport | None = None

    # ── Audio ──
    vo_direction: VODirection | None = None
    voiceover_path: str | None = None
    captions_path: str | None = None
    audio_duration_sec: float | None = None

    # ── Post-production ──
    post_brief: PostBrief | None = None
    edit_decisions: EditDecisionList | None = None
    picture_lock: PictureLockCertificate | None = None
    animatic_path: str | None = None
    motion_plan: MotionPlan | None = None
    color_grade: ColorPlan | None = None
    sound_plan: SoundPlan | None = None
    caption_style: CaptionStyle | None = None
    video_spec: VideoSpec | None = None

    # ── Storyboard Verification ──
    storyboard_stills: list[str] = Field(default_factory=list)
    storyboard_critique: dict[str, Any] = Field(default_factory=dict)

    # ── QC ──
    continuity_report: ContinuityReport | None = None
    qc_verdict: QCVerdict | None = None
    dailies_report: DailiesReport | None = None
    revision_notes: list[RevisionNotes] = Field(default_factory=list)
    revision_count: int = 0
    simplified_delivery: bool = False
    qc_passed: bool = False

    # ── Delivery ──
    delivery: DeliveryManifest | None = None

    # ── Loop Engineering ──
    flywheel_context: list[str] = Field(default_factory=list)
    component_evals: dict[str, EvalResult] = Field(default_factory=dict)
    run_scorecard: RunScorecard | None = None
    trace_path: str | None = None

    # ── CLI flags ──
    non_interactive: bool = False
    force_research: bool = False
    skip_research: bool = False

    @model_validator(mode="after")
    def sync_run_id(self) -> ProductionState:
        if not self.run_id:
            self.run_id = self.id
        return self

    def run_output(self) -> Path:
        settings = get_settings()
        if self.output_dir:
            base = Path(self.output_dir)
            if not base.is_absolute():
                base = settings.root / base
        else:
            base = settings.output_dir / self.id
        base.mkdir(parents=True, exist_ok=True)
        return base
