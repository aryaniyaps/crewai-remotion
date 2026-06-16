from __future__ import annotations

from crewai import Agent

from crewai_remotion.crews._common import _load_reference
from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import CreativeBrief
from crewai_remotion.models.visual_development import ComposedFrames


def run_creative_review_crew(
    composed: ComposedFrames,
    creative_brief: CreativeBrief,
    brand: BrandProfile,
) -> dict:
    """Creative Review: CD + Art Director + Compositor table-read for visuals."""
    llm = get_llm()
    comp_ref = _load_reference("composition.md")
    layout_ref = _load_reference("layout_vertical.md")

    composed_json = composed.model_dump_json()

    cd = Agent(
        role="Creative Director (Review)",
        goal="Review ComposedFrames against the creative brief — does this execute the vision?",
        backstory=f"Creative Director chairs the table read. Brief: {creative_brief.key_message}. "
                  "You identify what's weak and must improve before audio spend.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import CreativeReviewNotes
    cd_notes: CreativeReviewNotes = cd.kickoff(
        f"Creative Brief: {creative_brief.model_dump_json()}\n"
        f"ComposedFrames: {composed_json}\n"
        "Score brief_execution_score 0-1. List prioritized_issues (most critical first). "
        "Set approved=true only if no blocking issues.",
        response_format=CreativeReviewNotes,
    ).pydantic

    ad = Agent(
        role="Art Director (Review)",
        goal="Check visual cohesion across all beats — does the palette, mood, and style stay consistent?",
        backstory=f"Brand colors: primary={brand.visual.primary}, secondary={brand.visual.secondary}. "
                  "You catch when beat 3 suddenly changes visual language.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import ArtReviewNotes
    ad_notes: ArtReviewNotes = ad.kickoff(
        f"ComposedFrames: {composed_json}\n"
        f"Brand: {brand.name}, motion_style={brand.visual.motion_style}\n"
        "Score visual_cohesion_score 0-1. List issues per beat where visual language drifts.",
        response_format=ArtReviewNotes,
    ).pydantic

    compositor = Agent(
        role="Compositor (Review)",
        goal="Check composition readability on mobile — safe zones, focal points, negative space",
        backstory=f"{comp_ref[:400]} {layout_ref[:300]} "
                  "You verify every beat's composition works at arm's length on a phone.",
        llm=llm,
        verbose=True,
    )
    from crewai_remotion.models.visual_development import LayoutReviewNotes
    layout_notes: LayoutReviewNotes = compositor.kickoff(
        f"ComposedFrames: {composed_json}\n"
        "Score readability_score 0-1. Check: safe_margin_ok on every beat, "
        "negative_space_ratio ≥ 0.25 for minimal brands, no danger zone violations, "
        "focal_point declared for every beat. List issues per beat.",
        response_format=LayoutReviewNotes,
    ).pydantic

    return {
        "creative_review": cd_notes,
        "art_review": ad_notes,
        "layout_review": layout_notes,
    }
