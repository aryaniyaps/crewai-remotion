from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import ClarificationQuestionnaire


def run_topic_clarifier(topic: str, brand: BrandProfile) -> ClarificationQuestionnaire:
    llm = get_llm()
    agent = Agent(
        role="Topic Clarifier",
        goal="Generate 2-4 targeted CLI questions when a topic is structured but underspecified",
        backstory="You never use web search — you ask the human what they mean.",
        llm=llm,
        verbose=True,
    )
    task = Task(
        description=(
            f"Topic: {topic}\nBrand tone: {brand.voice.tone}\n"
            "If topic has count+category without named items (e.g. '3 AI tools'), ask which items, angle, audience."
        ),
        expected_output="ClarificationQuestionnaire with questions list",
        agent=agent,
        output_pydantic=ClarificationQuestionnaire,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    return crew.kickoff().pydantic  # type: ignore[return-value]
