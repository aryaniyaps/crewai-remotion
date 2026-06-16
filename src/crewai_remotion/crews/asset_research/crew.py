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
        goal="Define precise image search queries per scene beat for vertical video",
        backstory=(
            "You pick searchable queries for product logos, UI screenshots, or stock photos. "
            "Use serper_image_search to validate queries return usable vertical-friendly images."
        ),
        llm=llm,
        tools=[SerperImageSearchTool()],
        verbose=True,
    )
    beats_desc = json.dumps([{"beat_id": b.beat_id, "type": b.beat_type, "text": b.on_screen_text or b.vo_line} for b in script.beats])
    task = Task(
        description=(
            f"Topic: {topic}\nBrand: {brand.name} ({brand.visual.primary})\nBeats: {beats_desc}\n"
            "For each point/stat/hook beat, output SceneImageQuery with beat_id, search_query, visual_rationale. "
            "Prefer official logos or clean product photos. Use image search tool to sanity-check queries."
        ),
        expected_output="AssetResearchBrief with scene_queries list",
        agent=researcher,
        output_pydantic=AssetResearchBrief,
    )
    crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return result.pydantic  # type: ignore[return-value]
