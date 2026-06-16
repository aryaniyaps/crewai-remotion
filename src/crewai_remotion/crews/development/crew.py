from __future__ import annotations

from crewai import Agent

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import (
    CreativeBrief,
    ComplexityBudget,
    RetentionBeatSheet,
)


def run_development_crew(topic: str, brand: BrandProfile, duration_sec: float) -> tuple[CreativeBrief, ComplexityBudget, RetentionBeatSheet]:
    llm = get_llm()
    strategist = Agent(
        role="Content Strategist",
        goal="Produce a tight creative brief and retention beat sheet for a short vertical video",
        backstory="You think in hooks, pattern interrupts, and mobile attention spans.",
        llm=llm,
        verbose=True,
    )
    brief = strategist.kickoff(
        (
            f"Topic: {topic}\nBrand: {brand.name}, tone {brand.voice.tone}\n"
            f"Duration: {duration_sec}s vertical 9:16\n"
            "Write objective, audience, key_message, tone_notes, cta. Set approved=true."
        ),
        response_format=CreativeBrief,
    ).pydantic
    budget = strategist.kickoff(
        f"Set complexity budget for {duration_sec}s video (max beats, lottie, motion layers, words). approved=true.",
        response_format=ComplexityBudget,
    ).pydantic
    beats = strategist.kickoff(
        "Retention beat sheet: hook_window_sec=3, beats list, pattern_interrupts for vertical social.",
        response_format=RetentionBeatSheet,
    ).pydantic
    return brief, budget, beats
