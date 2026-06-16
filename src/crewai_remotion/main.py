from __future__ import annotations

from pathlib import Path

from crewai.flow.flow import Flow, listen, start

from crewai_remotion.errors import ProductionError
from crewai_remotion.models.brand import load_brand
from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.pipeline.runner import run_production
from crewai_remotion.loops.flywheel import recall_lessons


def coerce_production_state(raw: object) -> ProductionState:
    if isinstance(raw, ProductionState):
        return raw
    if hasattr(raw, "model_dump"):
        return ProductionState.model_validate(raw.model_dump(mode="json"))
    if isinstance(raw, dict):
        return ProductionState.model_validate(raw)
    raise ProductionError(
        "Could not read production state after flow completed",
        phase="flow",
        hint="Re-run with --verbose or inspect traces/ under the run output folder.",
    )


class ProductionFlow(Flow[ProductionState]):
    """Executive Producer Flow — CrewAI orchestrates the full production pipeline."""

    @start()
    def recall_lessons_step(self) -> ProductionState:
        recall_lessons(self.state)
        return self.state

    @listen(recall_lessons_step)
    def run_pipeline(self) -> ProductionState:
        return run_production(self.state, render=True)


def kickoff_production(state: ProductionState) -> ProductionState:
    run_dir = str(state.run_output())
    try:
        flow = ProductionFlow()
        flow.kickoff(inputs=state.model_dump(mode="json"))
        return coerce_production_state(flow.state)
    except ProductionError:
        raise
    except Exception as exc:
        raise ProductionError(
            str(exc) or "CrewAI flow execution failed",
            phase="flow",
            hint=(
                "Check .env for OPENAI_API_KEY, output folder production_notes.jsonl, "
                "and traces/. For Remotion issues run: cd remotion && npm install"
            ),
            run_dir=run_dir,
        ) from exc


def build_state(
    *,
    topic: str,
    brand_path: Path,
    duration_sec: float = 30.0,
    non_interactive: bool = False,
    force_research: bool = False,
    skip_research: bool = False,
) -> ProductionState:
    brand = load_brand(brand_path)
    return ProductionState(
        topic=topic,
        duration_sec=duration_sec,
        brand_path=str(brand_path),
        brand=brand,
        non_interactive=non_interactive,
        force_research=force_research,
        skip_research=skip_research,
    )
