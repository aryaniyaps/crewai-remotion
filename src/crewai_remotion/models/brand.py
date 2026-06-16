from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class VoiceConfig(BaseModel):
    tone: list[str] = Field(default_factory=lambda: ["bold", "direct"])
    avoid_words: list[str] = Field(default_factory=list)
    hook_patterns: list[str] = Field(default_factory=lambda: ["question", "stat-shock"])


class VisualConfig(BaseModel):
    primary: str = "#FF3366"
    secondary: str = "#1A1A2E"
    accent: str = "#FFD700"
    surface: str = "#0F0F14"
    caption_highlight: str = "#39E508"
    font_heading: str = "Inter"
    font_body: str = "Inter"
    font_weights: list[int] = Field(default_factory=lambda: [400, 700])
    motion_style: Literal["snappy", "smooth", "kinetic"] = "snappy"
    text_density: Literal["minimal", "balanced", "dense"] = "minimal"
    texture: Literal["none", "grain", "paper"] = "grain"


class AssetsConfig(BaseModel):
    logo: str | None = None
    hero_image: str | None = None
    lottie_overrides: dict[str, str] = Field(default_factory=dict)
    remove_background: bool = False


class AudioConfig(BaseModel):
    tts_provider: Literal["piper", "f5-tts", "elevenlabs"] = "piper"
    voice: str = "en_US-lessac-medium"
    tts_clone_sample: str | None = None  # path to reference voice sample for cloning
    music_mood: Literal["upbeat", "calm", "dramatic"] = "upbeat"
    music_volume: float = 0.25

    @field_validator("tts_provider", mode="before")
    @classmethod
    def normalize_tts_provider(cls, v: object) -> str:
        if v in ("openai", None):
            return "piper"
        return str(v)

    @field_validator("voice", mode="before")
    @classmethod
    def normalize_voice(cls, v: object) -> str:
        from crewai_remotion.tools.piper_tts import resolve_piper_voice

        return resolve_piper_voice(str(v or ""))


class PlatformConfig(BaseModel):
    format: Literal["vertical"] = "vertical"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    safe_margin: int = 48


class SeriesConfig(BaseModel):
    intro_beat_template: str = "branded_sting"
    outro_beat_template: str = "cta_card"
    hook_style_preference: str = "question_led"


class QualityConfig(BaseModel):
    strict_qa: bool = False


class BrandProfile(BaseModel):
    name: str
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    visual: VisualConfig = Field(default_factory=VisualConfig)
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    platform: PlatformConfig = Field(default_factory=PlatformConfig)
    series: SeriesConfig | None = None
    quality: QualityConfig = Field(default_factory=QualityConfig)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Brand name cannot be empty")
        return v.strip()

    def slug(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return slug or "brand"


def load_brand(path: Path | str) -> BrandProfile:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return BrandProfile.model_validate(data)


def save_brand(profile: BrandProfile, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = profile.model_dump(mode="json", exclude_none=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def brand_dir_for_slug(root: Path, slug: str) -> Path:
    return root / "brands" / slug


def default_brand_path(root: Path, slug: str) -> Path:
    return brand_dir_for_slug(root, slug) / f"{slug}.brand.yaml"


def copy_logo(src: Path, brand_dir: Path) -> str | None:
    if not src.exists():
        return None
    dest = brand_dir / "logo.svg"
    shutil.copy2(src, dest)
    return str(dest.relative_to(brand_dir.parent.parent))
