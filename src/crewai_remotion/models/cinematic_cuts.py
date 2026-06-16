from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CutType(str, Enum):
    HARD_CUT = "hard_cut"
    JUMP_CUT = "jump_cut"
    MATCH_CUT = "match_cut"
    SMASH_CUT = "smash_cut"
    CUT_ON_ACTION = "cut_on_action"
    J_CUT = "j_cut"
    L_CUT = "l_cut"
    CROSS_CUT = "cross_cut"
    MONTAGE = "montage"
    DISSOLVE = "dissolve"
    INVISIBLE_CUT = "invisible_cut"


class SplitEdit(str, Enum):
    NONE = "none"
    J_CUT = "j_cut"
    L_CUT = "l_cut"


class AudioSyncEvent(str, Enum):
    PHRASE_END = "phrase_end"
    EMPHASIS_WORD = "emphasis_word"
    DOWNBEAT = "downbeat"
    BREATH_PAUSE = "breath_pause"
    PHRASE_START = "phrase_start"


class CutOut(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    """Per-beat-boundary cut specification — validated by Gate PictureLock."""
    cut_type: CutType = CutType.HARD_CUT
    split_edit: SplitEdit = SplitEdit.NONE
    audio_lead_frames: int = Field(default=0, ge=0, le=15)
    audio_trail_frames: int = Field(default=0, ge=0, le=15)
    audio_sync_ref: str = ""
    audio_sync_event: AudioSyncEvent = AudioSyncEvent.PHRASE_END
    cut_on_action_frame: int | None = None
    notes: str = ""



class SyncMarker(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    frame: int
    event: Literal["downbeat", "snare", "phrase_start"]
    use_for: Literal["major_cut", "accent_only"]


class EditDecision(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    """Legacy per-beat decision — kept for backward compat, prefer CutOut."""
    scene_id: str
    cut_type: CutType = CutType.HARD_CUT
    split_edit: SplitEdit = SplitEdit.NONE
    audio_sync_ref: str = ""
    offset_frames: int = 0
    notes: str = ""


class EditDecisionList(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    decisions: list[EditDecision] = Field(default_factory=list)
    pacing_notes: str = ""


class PictureLockCertificate(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    """Issued by Post Supervisor after Editor locks timing."""
    approved: bool = False
    total_frames: int = 0
    audio_duration_sec: float = 0.0
    frame_drift: int = 0  # sum(beat_durations) - audio_frames
    editor_notes: str = ""


class ChangeOrder(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    """Requested change after creative brief lock — requires Producer approval."""
    field_changed: str
    reason: str
    departments_affected: list[str] = Field(default_factory=list)
    approved: bool = False



# ── Cut Range Constants ──

J_CUT_LEAD_RANGE = {"min": 3, "max": 8}
L_CUT_TRAIL_RANGE = {"min": 4, "max": 15}
MAX_SMASH_CUTS_PER_30S = 1