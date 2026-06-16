from __future__ import annotations

import typer
from rich.console import Console

from crewai_remotion.models.development import ClarificationQuestion, ClarificationQuestionnaire, TopicClarification

console = Console()


def run_topic_prompts(
    raw_topic: str,
    questionnaire: ClarificationQuestionnaire,
) -> TopicClarification:
    console.print("\n[bold]Topic clarification[/bold]")
    console.print("Topic looks structured but underspecified. A few quick questions:\n")

    answers: dict[str, str] = {}
    try:
        for q in questionnaire.questions:
            if q.choices:
                for i, choice in enumerate(q.choices, 1):
                    console.print(f"  {i}. {choice}")
                raw = typer.prompt(q.prompt)
                if raw.isdigit() and 1 <= int(raw) <= len(q.choices):
                    answers[q.id] = q.choices[int(raw) - 1]
                else:
                    answers[q.id] = raw
            else:
                answers[q.id] = typer.prompt(q.prompt, default="")
    except (typer.Abort, EOFError, KeyboardInterrupt):
        console.print(
            "[yellow]No TTY input — using original topic. "
            "Pass --non-interactive to skip prompts.[/yellow]"
        )
        return TopicClarification(raw_topic=raw_topic, effective_topic=raw_topic)

    effective = _merge_topic(raw_topic, answers)
    return TopicClarification(raw_topic=raw_topic, answers=answers, effective_topic=effective)


def _merge_topic(raw: str, answers: dict[str, str]) -> str:
    parts = [v for v in answers.values() if v.strip() and v.lower() not in ("you pick", "skip", "")]
    if not parts:
        return raw
    if "tools" in raw.lower() and any("," in p or " " in p for p in parts):
        tools = answers.get("tools", answers.get("q1", ""))
        angle = answers.get("angle", answers.get("q2", ""))
        audience = answers.get("audience", answers.get("q3", ""))
        if tools:
            base = tools if "for" in tools else f"{tools}"
            extras = [x for x in [angle, audience] if x]
            if extras:
                return f"{base} — {'; '.join(extras)}"
            return base
    return f"{raw} ({'; '.join(parts)})"
