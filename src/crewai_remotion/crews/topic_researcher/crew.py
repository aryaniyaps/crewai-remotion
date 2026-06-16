from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import TopicResearchBrief
from crewai_remotion.tools.crewai_tools import SerperWebSearchTool


def run_topic_researcher(topic: str, brand: BrandProfile) -> TopicResearchBrief:
    llm = get_llm()
    researcher = Agent(
        role="Topic Researcher",
        goal="Find concrete facts, named entities, and angles for an underspecified video topic",
        backstory="You research via Serper and return structured briefs — never invent sources.",
        llm=llm,
        tools=[SerperWebSearchTool()],
        verbose=True,
    )
    task = Task(
        description=(
            f"Research the topic: {topic}\n"
            f"Brand tone: {', '.join(brand.voice.tone)}\n"
            "Use serper_web_search up to 3 times. Return refined angles, key facts, and source URLs."
        ),
        expected_output="TopicResearchBrief JSON with refined_angles, key_facts, sources",
        agent=researcher,
        output_pydantic=TopicResearchBrief,
    )
    crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    return result.pydantic  # type: ignore[return-value]
