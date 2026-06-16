from __future__ import annotations

from crewai import Agent

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.visual_development import ComposedFrames, StyleBible
from crewai_remotion.models.writers_room import AVScript


def run_clearance_crew(
    composed: ComposedFrames,
    style_bible: StyleBible | None,
    brand: BrandProfile,
    av_script: AVScript | None = None,
) -> dict:
    """Clearance: Pipeline TD + Brand Guardian — pre-audio feasibility and brand compliance."""
    llm = get_llm()

    composed_json = composed.model_dump_json()

    # Pipeline TD
    pipeline_td = Agent(
        role="Pipeline TD",
        goal="Validate ComposedFrames against Remotion capabilities — catch impossible specs early",
        backstory="Technical supervisor. You know exactly what Remotion can and cannot render. "
                  "You catch Lottie IDs that don't exist, effect combinations that crash, "
                  "and beat counts that exceed render limits.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import FeasibilityReport
    feasibility: FeasibilityReport = pipeline_td.kickoff(
        f"ComposedFrames: {composed_json}\n"
        "Check: beat count ≤ 8, all scene_types are valid Remotion scenes, "
        "all illustration_ids look like valid catalog references, "
        "no unsupported effect combinations. Output passes=true only if no blockers.",
        response_format=FeasibilityReport,
    ).pydantic

    # Brand Guardian
    brand_guardian = Agent(
        role="Brand Guardian",
        goal="Adversarial brand check — only rejects, never creates. Every violation must cite the brand YAML rule.",
        backstory="Brand compliance officer. Your job is to say NO. "
                  f"Brand rules: primary={brand.visual.primary}, tone={brand.voice.tone}, "
                  f"avoid_words={brand.voice.avoid_words}, motion={brand.visual.motion_style}. "
                  "You catch when the creative team drifts from the brand book.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import BrandComplianceReport
    compliance: BrandComplianceReport = brand_guardian.kickoff(
        f"Brand YAML: {brand.model_dump_json()}\n"
        f"ComposedFrames: {composed_json}\n"
        f"AVScript: {av_script.model_dump_json() if av_script else 'N/A'}\n"
        "Check: colors used are from brand palette, tone matches voice spec, "
        "no avoid_words in headlines or VO, motion_style consistent. "
        "Only reject with specific YAML rule citation. Output passes=true only if zero violations.",
        response_format=BrandComplianceReport,
    ).pydantic

    return {
        "feasibility": feasibility,
        "brand_compliance": compliance,
    }
