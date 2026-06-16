from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator

from crewai_remotion.models.cinematic_cuts import CutType, EditDecisionList


class MotionGraphicSpec(BaseModel):
    """A single motion graphic element for a scene.

    The ``config`` field is typed as ``str`` for OpenAI structured-output
    compatibility (dict[str,Any] lacks ``additionalProperties: false``).
    A field-serializer converts it back to a dict when serializing for
    Remotion, so the TS side never sees a raw string.
    """
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    id: str
    type: str
    config: str = Field(
        default="{}",
        description="JSON string of motion graphic configuration (e.g. '{\"count\": 20, \"speed\": 0.4}')",
    )
    entry_frame: int = 0
    exit_frame: int | None = None

    @field_validator("config", mode="before")
    @classmethod
    def _coerce_config(cls, v: object) -> str:
        """Accept either a dict (from LLM) or a pre-serialized string."""
        import json as _json
        if isinstance(v, dict):
            return _json.dumps(v)
        if isinstance(v, str):
            return v
        return _json.dumps(v) if v else "{}"

    @field_serializer("config", when_used="json")
    def _serialize_config(self, value: str) -> dict[str, Any]:
        import json as _json
        try:
            return _json.loads(value) if value else {}
        except (TypeError, ValueError):
            return {}

    @property
    def config_dict(self) -> dict[str, Any]:
        """Convenience accessor: parsed config dict (non-serialized)."""
        import json as _json
        try:
            return _json.loads(self.config) if self.config else {}
        except (TypeError, ValueError):
            return {}

class SceneSpec(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    id: str
    type: str
    headline: str
    subhead: str = ""
    duration_frames: int = 90
    illustration_id: str | None = None
    image_path: str | None = None
    background_variant: str = "primary"
    layout: str = "center_stack"
    motion_intent: str = "enter_up"
    cut_type: CutType = CutType.HARD_CUT
    motion_graphics: list[MotionGraphicSpec] = Field(default_factory=list)
    motion_intensity: str = "medium"  # low, medium, high
    parallax_depth: float = 0.0  # 0-1
    camera_motion: str = "none"  # none, push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, handheld



class CaptionWord(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    text: str
    start_ms: int
    end_ms: int


class CaptionSegment(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    words: list[CaptionWord] = Field(default_factory=list)




class SfxCueSpec(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    """A single sound effect cue at a specific frame."""
    frame: int
    src: str
    volume: float = 0.7
    cut_type: str | None = None



class SfxSpec(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    cues: list[SfxCueSpec] = Field(default_factory=list)


class ThemeTokens(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    primary: str
    secondary: str
    accent: str
    surface: str
    caption_highlight: str
    font_heading: str
    font_body: str
    motion_style: str
    texture: str


class AudioSpec(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    voiceover: str = ""
    music_path: str = ""
    music_mood: str = ""
    music_volume: float = 0.25
    duration_sec: float = 30.0
    sfx: SfxSpec = Field(default_factory=SfxSpec)


class VideoSpec(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    title: str
    width: int = 1080
    height: int = 1920
    fps: int = 30
    duration_frames: int = 900
    theme: ThemeTokens
    scenes: list[SceneSpec] = Field(default_factory=list)
    captions: list[CaptionSegment] = Field(default_factory=list)
    edit_decisions: EditDecisionList = Field(default_factory=EditDecisionList)
    audio: AudioSpec = Field(default_factory=AudioSpec)

    def to_remotion_props(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
