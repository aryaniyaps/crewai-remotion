from __future__ import annotations

import json

from crewai import Agent, Crew, Process, Task

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.asset_research import AssetResearchBrief
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.writers_room import AVScript
from crewai_remotion.tools.crewai_tools import SerperImageSearchTool


def run_asset_research_crew(
    topic: str,
    brand: BrandProfile,
    script: AVScript,
) -> AssetResearchBrief:
    llm = get_llm()
    researcher = Agent(
        role="Visual Asset Researcher",
        goal="Define concrete subject-driven image search queries per scene beat for vertical video",
        backstory=(
            "You pick searchable queries for one clear visual subject per beat: data center building exterior, "
            "server rack, power grid, semiconductor wafer, globe fiber network, city buildings, or another concrete object implied by the script. "
            "Prefer isolated subject photos or illustrations with a clear main object and vertical-friendly composition. "
            "Avoid abstract stock backgrounds, generic gradients, empty tech textures, and decorative-only imagery. "
            "Use serper_image_search to validate queries return usable subject references."
        ),
        llm=llm,
        tools=[SerperImageSearchTool()],
        verbose=True,
    )
    beats_desc = json.dumps([{"beat_id": b.beat_id, "type": b.beat_type, "text": b.on_screen_text or b.vo_line} for b in script.beats])
    task = Task(
        description=(
            f"Topic: {topic}\nBrand: {brand.name} ({brand.visual.primary})\nBeats: {beats_desc}\n"
            "For every beat, output SceneImageQuery with beat_id, search_query, visual_rationale, preferred_style. "
            "Each search_query must name a concrete main subject/object plus useful qualifiers such as isolated, cutout, exterior, close-up, photo reference, illustration reference, vertical composition, or transparent background. "
            "visual_rationale must state the subject the scene will animate. Prefer official logos/screenshots only when the beat is specifically about a product or UI; otherwise prefer concrete subject photos/illustrations. "
            "Do not request abstract stock backgrounds, waves, particles, blurred lights, or generic motion-graphic textures. Use image search tool to sanity-check queries."
        ),
        expected_output="AssetResearchBrief with scene_queries list",
        agent=researcher,
        output_pydantic=AssetResearchBrief,
    )
    crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return result.pydantic  # type: ignore[return-value]
