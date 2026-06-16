from __future__ import annotations

import os

from crewai import LLM

from crewai_remotion.config import get_settings


def get_llm() -> LLM:
    settings = get_settings()
    if settings.openai_api_key:
        return LLM(model=f"openai/{settings.openai_model_name}", api_key=settings.openai_api_key)
    if os.getenv("ANTHROPIC_API_KEY"):
        model = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-20241022")
        return LLM(model=f"anthropic/{model}")
    raise RuntimeError("OPENAI_API_KEY or ANTHROPIC_API_KEY required for CrewAI agents")
