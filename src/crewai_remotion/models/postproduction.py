from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from crewai_remotion.models.cinematic_cuts import CutOut, SyncMarker


# ── Post Supervisor ──

class PostBrief(BaseModel):
    """Post Supervisor briefs the edit bay — constraints for all post roles."""
    no_layout_changes: bool = True
    picture_lock_required: bool = True
    vo_primary_sync: bool = True
    motion_intensity: Literal["low", "medium", "high"] = "medium"
    constraints: list[str] = Field(default_factory=list)


# ── Editor ──

class BeatDuration(BaseModel):
    beat_id: str
    frames: int


class BeatMotion(BaseModel):
    beat_id: str
    motion: str


class CutActionFrame(BaseModel):
    beat_id: str
    cut_on_action_frame: int


class EditDecisionListV2(BaseModel):
    """Editor's final cut list — per-beat-boundary cuts with real timestamps."""
    cuts: list[CutOut] = Field(default_factory=list)
    beat_durations: list[BeatDuration] = Field(default_factory=list)
    total_frames: int = 0
    audio_duration_sec: float = 0.0
    retention_anchors_hit: list[str] = Field(default_factory=list)
    pacing_notes: str = ""


# ── Motion Designer ──

class MotionPlan(BaseModel):
    """Motion Designer implements Editor's cuts as Remotion transitions."""
    global_style: Literal["snappy", "smooth", "kinetic"] = "snappy"
    beat_motions: list[BeatMotion] = Field(default_factory=list)
    stagger_ms: int = 60
    cut_on_action_frames: list[CutActionFrame] = Field(default_factory=list)
    notes: str = ""


# ── Colorist ──

class ColorGrade(BaseModel):
    """Colorist per-beat color grading intent."""
    beat_id: str = ""
    bg_saturation: float = Field(default=0.8, ge=0.0, le=1.0)
    accent_boost: float = Field(default=0.2, ge=0.0, le=1.0)
    text_contrast_tier: Literal["high", "aa", "fail"] = "aa"


class ColorPlan(BaseModel):
    """Colorist output — per-beat grade map."""
    grades: list[ColorGrade] = Field(default_factory=list)
    notes: str = ""


# ── Sound Designer ──

class SfxCue(BaseModel):
    """A single sound effect triggered at a specific frame."""
    frame: int  # frame number in the composition
    sfx_id: str  # e.g. 'whoosh', 'impact', 'pop', 'whoosh_low', 'click', 'swoosh'
    volume: float = 0.7  # 0-1
    cut_type: str | None = None  # which cut this SFX accompanies
    notes: str = ""


class SfxOnCut(BaseModel):
    """Deprecated — use SfxCue instead.  Kept for backward compat with older crew output."""
    cut_type: str = ""
    sfx: str = ""


class DuckingPoint(BaseModel):
    frame: int = 0
    volume: float = 0.25


class SoundPlan(BaseModel):
    """Sound Designer output — music, ducking, sync markers, SFX."""
    music_track_id: str = ""
    music_volume: float = Field(default=0.25, ge=0.0, le=1.0)
    bpm: float = 120.0
    sync_markers: list[SyncMarker] = Field(default_factory=list)
    sfx_cues: list[SfxCue] = Field(default_factory=list)
    sfx_on_cuts: list[SfxOnCut] = Field(
        default_factory=list,
        description="DEPRECATED: Use sfx_cues instead. Preserved for backward compat with older crew output.",
    )
    ducking_curve: list[DuckingPoint] = Field(default_factory=list)
    notes: str = ""


# ── Caption Designer ──

class CaptionStyle(BaseModel):
    """Caption Designer output — TikTok-native caption rhythm."""
    combine_ms: int = 800
    highlight_color: str = "#39E508"
    font: str = "Inter"
    position: Literal["bottom", "top", "center"] = "bottom"
    tier: Literal["display", "headline", "body", "caption"] = "caption"
    notes: str = ""


# ── Voice Director ──

class PhraseBoundary(BaseModel):
    beat_id: str
    phrase_end_frame_hint: int


class VODirection(BaseModel):
    """Voice Director annotates AVScript for TTS — pace, emphasis, pauses."""
    pacing: str = "conversational"
    emphasis_words: list[str] = Field(default_factory=list)
    pause_after_ms: int = 300
    energy: Literal["low", "medium", "high"] = "medium"
    phrase_boundaries: list[PhraseBoundary] = Field(default_factory=list)
    notes: str = ""


# ── Delivery ──

class DeliveryManifest(BaseModel):
    video_path: str = ""
    spec_path: str = ""
    captions_path: str = ""
    script_path: str = ""
    thumbnail_path: str = ""
    asset_manifest_path: str = ""
    qc_signoff_path: str = ""
    run_id: str = ""
    branded: bool = False
