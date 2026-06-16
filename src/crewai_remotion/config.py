from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")

    openai_api_key: str | None = None
    openai_model_name: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    piper_voice: str = "en_US-lessac-medium"
    piper_data_dir: str = "assets/piper-voices"
    elevenlabs_api_key: str = Field(default="")
    serper_api_key: str | None = None
    remotion_project_path: str = "remotion"

    @property
    def root(self) -> Path:
        return ROOT

    @property
    def output_dir(self) -> Path:
        return ROOT / "output"

    @property
    def brands_dir(self) -> Path:
        return ROOT / "brands"

    @property
    def has_llm(self) -> bool:
        return bool(self.openai_api_key or os.getenv("ANTHROPIC_API_KEY"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
