from __future__ import annotations

from crewai_remotion.cli.topic_prompts import run_topic_prompts
from crewai_remotion.gates.topic_ambiguity import is_ambiguous
from crewai_remotion.models.development import (
    ClarificationQuestion,
    ClarificationQuestionnaire,
    TopicClarification,
    TopicResearchBrief,
)
from crewai_remotion.models.production_state import ProductionState


def build_questionnaire(topic: str, brand) -> ClarificationQuestionnaire:
    from crewai_remotion.crews.topic_clarifier.crew import run_topic_clarifier

    try:
        return run_topic_clarifier(topic, brand)
    except Exception:
        return default_questionnaire(topic)


def default_questionnaire(topic: str) -> ClarificationQuestionnaire:
    questions = []
    if "tools" in topic.lower() or "apps" in topic.lower():
        questions = [
            ClarificationQuestion(
                id="tools",
                prompt="Which tools should we feature? (comma-separated, or 'you pick')",
            ),
            ClarificationQuestion(
                id="angle",
                prompt="What's the angle — save time, ship faster, raise funding?",
                choices=["save time", "ship faster", "raise funding", "reduce cost"],
            ),
            ClarificationQuestion(
                id="audience",
                prompt="Who is the viewer?",
                choices=["first-time founders", "SaaS founders", "all founders", "developers"],
            ),
        ]
    else:
        questions = [
            ClarificationQuestion(id="angle", prompt="What's the main angle or takeaway?"),
            ClarificationQuestion(id="audience", prompt="Who is this for?"),
        ]
    return ClarificationQuestionnaire(questions=questions, rationale="Topic lacks concrete content")


def run_topic_pipeline(state: ProductionState) -> ProductionState:
    topic = state.topic
    if state.skip_research and not is_ambiguous(topic):
        state.effective_topic = topic
        return state

    if not is_ambiguous(topic) and not state.force_research:
        state.effective_topic = topic
        return state

    assert state.brand is not None
    state.questionnaire = build_questionnaire(topic, state.brand)

    if state.non_interactive:
        state.topic_clarification = TopicClarification(raw_topic=topic, effective_topic=topic)
        state.effective_topic = topic
        if is_ambiguous(topic) or state.force_research:
            state = _run_topic_research(state)
        return state

    state.topic_clarification = run_topic_prompts(topic, state.questionnaire)
    state.effective_topic = state.topic_clarification.effective_topic

    if is_ambiguous(state.effective_topic) or state.force_research:
        state = _run_topic_research(state)

    return state


def _run_topic_research(state: ProductionState) -> ProductionState:
    from crewai_remotion.crews.pipeline_crews import run_topic_researcher
    from crewai_remotion.tools.serper_client import SerperError

    assert state.brand is not None
    topic = state.effective_topic or state.topic
    try:
        state.topic_research = run_topic_researcher(topic, state.brand)
        state.effective_topic = _research_to_topic(topic, state.topic_research)
    except SerperError as exc:
        if state.non_interactive and state.force_research:
            raise RuntimeError(str(exc)) from exc
        state.topic_research = TopicResearchBrief(
            refined_angles=[topic],
            key_facts=[],
            sources=[],
        )
    return state


def _research_to_topic(base: str, brief: TopicResearchBrief) -> str:
    if brief.key_facts:
        return f"{', '.join(brief.key_facts[:3])} — {base}"
    return base
