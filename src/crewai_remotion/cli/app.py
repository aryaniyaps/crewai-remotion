from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from crewai_remotion.cli.brand_resolve import resolve_brand, set_active_brand
from crewai_remotion.cli.errors import report_error
from crewai_remotion.cli.preflight import require_production_keys, require_runtime_deps
from crewai_remotion.cli.validate import validate_run
from crewai_remotion.cli.brand_wizard import run_brand_wizard
from crewai_remotion.config import get_settings
from crewai_remotion.main import build_state, kickoff_production
from crewai_remotion.models.brand import load_brand, save_brand
from crewai_remotion.pipeline.runner import run_production
from crewai_remotion.tools.render_remotion import render_video

app = typer.Typer(no_args_is_help=True, help="Agentic social video CLI — CrewAI + Remotion")
brand_app = typer.Typer(help="Brand profile management")
loop_app = typer.Typer(help="Loop engineering flywheel")
app.add_typer(brand_app, name="brand")
app.add_typer(loop_app, name="loop")

console = Console()


def _effective_non_interactive(non_interactive: bool) -> bool:
    if non_interactive:
        return True
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        console.print("[dim]Non-TTY session — running in non-interactive mode.[/dim]")
        return True
    return False


@app.command()
def create(
    topic: str = typer.Option(..., "--topic", "-t", help="Video topic"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Brand YAML path"),
    duration: float = typer.Option(30.0, "--duration", "-d", help="Target duration in seconds"),
    research: bool = typer.Option(False, "--research", help="Force topic research path"),
    no_research: bool = typer.Option(False, "--no-research", help="Skip research entirely"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="CI mode — no TTY prompts"),
    no_render: bool = typer.Option(False, "--no-render", help="Stop after spec generation"),
    strict_qa: bool = typer.Option(False, "--strict-qa", help="Fail pipeline if Visual QA fails"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print full traceback on failure"),
) -> None:
    """Run full production pipeline: brand → topic → crews → render."""
    try:
        require_production_keys()
        require_runtime_deps(need_render=not no_render)
        non_interactive = _effective_non_interactive(non_interactive)
        profile, brand_path = resolve_brand(brand, non_interactive=non_interactive)
        set_active_brand(brand_path)

        state = build_state(
            topic=topic,
            brand_path=brand_path,
            duration_sec=duration,
            non_interactive=non_interactive,
            force_research=research,
            skip_research=no_research,
        )
        state.brand = profile
        state.strict_qa_override = strict_qa

        console.print(f"[bold green]▶ Production run[/bold green] {state.run_id}")
        console.print(f"  Topic: {topic}")
        console.print(f"  Brand: {brand_path}")

        if no_render:
            state = run_production(state, render=False)
        else:
            state = kickoff_production(state)

        validate_run(state, expect_video=not no_render)
        _print_run_summary(state)
    except Exception as exc:
        report_error(exc, verbose=verbose)


def _print_run_summary(state) -> None:
    out = state.run_output()
    console.print(f"\n[bold green]Done.[/bold green] Output: {out}")
    delivery = state.delivery
    if delivery:
        video_path = (
            delivery.get("video_path")
            if isinstance(delivery, dict)
            else delivery.video_path
        )
        if video_path:
            console.print(f"  Video: {out / video_path}")
    elif (out / "video.mp4").exists():
        console.print(f"  Video: {out / 'video.mp4'}")
    console.print(f"  Spec:  {out / 'video_spec.json'}")


@app.command()
def plan(
    topic: str = typer.Option(..., "--topic", "-t"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b"),
    duration: float = typer.Option(30.0, "--duration", "-d"),
    non_interactive: bool = typer.Option(False, "--non-interactive"),
    research: bool = typer.Option(False, "--research"),
    no_research: bool = typer.Option(False, "--no-research"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate plan artifacts without render."""
    try:
        require_production_keys()
        require_runtime_deps(need_render=False)
        non_interactive = _effective_non_interactive(non_interactive)
        profile, brand_path = resolve_brand(brand, non_interactive=non_interactive)
        set_active_brand(brand_path)
        state = build_state(
            topic=topic,
            brand_path=brand_path,
            duration_sec=duration,
            non_interactive=non_interactive,
            force_research=research,
            skip_research=no_research,
        )
        state.brand = profile
        console.print(f"[bold green]▶ Plan run[/bold green] {state.run_id}")
        state = run_production(state, render=False)
        validate_run(state, expect_video=False)
        console.print(f"\n[bold green]Plan complete.[/bold green] Output: {state.run_output()}")
    except Exception as exc:
        report_error(exc, verbose=verbose)


@app.command("render")
def render_cmd(
    spec: Path = typer.Option(..., "--spec", help="Path to video_spec.json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Render MP4 from existing VideoSpec."""
    import json

    from crewai_remotion.models.video_spec import VideoSpec

    data = json.loads(spec.read_text(encoding="utf-8"))
    video_spec = VideoSpec.model_validate(data)
    state = build_state(topic="", brand_path=get_settings().root / "brands/default.brand.yaml")
    state.video_spec = video_spec
    state.output_dir = str(spec.parent)
    path = render_video(state)
    if output and path.exists():
        import shutil

        shutil.copy2(path, output)
    console.print(f"Rendered: {path}")


@brand_app.command("init")
def brand_init(
    slug: Optional[str] = typer.Argument(None, help="Optional slug hint"),
) -> None:
    """Interactive brand wizard."""
    profile, path = run_brand_wizard(slug_hint=slug, inline=False)
    set_active_brand(path)
    console.print(f"Active brand set to {path}")


@brand_app.command("edit")
def brand_edit(path: Path = typer.Argument(..., help="Brand YAML to edit")) -> None:
    existing = load_brand(path)
    profile, saved = run_brand_wizard(existing=existing, inline=False)
    save_brand(profile, saved)
    set_active_brand(saved)


@brand_app.command("list")
def brand_list() -> None:
    settings = get_settings()
    files = sorted(settings.brands_dir.glob("**/*.brand.yaml"))
    active = (settings.brands_dir / ".active").read_text(encoding="utf-8").strip() if (settings.brands_dir / ".active").exists() else ""
    for f in files:
        mark = " *" if str(f.relative_to(settings.root)) == active else ""
        console.print(f"  {f.relative_to(settings.root)}{mark}")


@brand_app.command("use")
def brand_use(slug: str = typer.Argument(...)) -> None:
    settings = get_settings()
    matches = list(settings.brands_dir.glob(f"**/{slug}*.brand.yaml"))
    if not matches:
        raise typer.BadParameter(f"No brand matching slug: {slug}")
    set_active_brand(matches[0])
    console.print(f"Active brand: {matches[0]}")


@brand_app.command("validate")
def brand_validate(path: Path = typer.Argument(...)) -> None:
    load_brand(path)
    console.print(f"[green]Valid:[/green] {path}")


@loop_app.command("status")
def loop_status() -> None:
    settings = get_settings()
    learnings = settings.root / "src" / "crewai_remotion" / "loops" / "learnings" / "global.yaml"
    console.print(f"Flywheel learnings: {learnings} ({'exists' if learnings.exists() else 'missing'})")


@loop_app.command("trace")
def loop_trace(
    run_id: str = typer.Argument(..., help="Run ID under output/"),
) -> None:
    """Pretty-print trace.jsonl for a run."""
    settings = get_settings()
    trace_path = settings.output_dir / run_id / "traces" / "trace.jsonl"
    if not trace_path.exists():
        console.print(f"[red]Trace not found: {trace_path}[/red]")
        raise typer.Exit(1)
    import json
    with trace_path.open() as f:
        for line in f:
            span = json.loads(line)
            icon = "✅" if span.get("status") == "ok" else "❌"
            err = f" — {span['error']}" if span.get("error") else ""
            console.print(f"  {icon} {span['phase']:25s} {span['duration_ms']:>6}ms{err}")


@loop_app.command("eval")
def loop_eval(
    run_id: str = typer.Argument(..., help="Run ID under output/"),
) -> None:
    """Re-run deterministic eval suite on saved artifacts."""
    from crewai_remotion.models.production_state import ProductionState
    from crewai_remotion.loops.evaluators.deterministic import run_deterministic_evals

    settings = get_settings()
    run_dir = settings.output_dir / run_id
    if not run_dir.exists():
        console.print(f"[red]Run not found: {run_dir}[/red]")
        raise typer.Exit(1)

    # Load state from saved artifacts
    import json
    state = ProductionState(id=run_id, topic="from-saved", run_id=run_id)
    spec_path = run_dir / "video_spec.json"
    if spec_path.exists():
        from crewai_remotion.models.video_spec import VideoSpec
        state.video_spec = VideoSpec(**json.loads(spec_path.read_text()))

    for phase in ["development", "writers_room", "visual_development", "postproduction", "qc"]:
        results = run_deterministic_evals(state, phase)
        for r in results:
            icon = "✅" if r.passed else "⚠️"
            console.print(f"  {icon} {r.name:30s} {r.message[:60]}")


@loop_app.command("regression")
def loop_regression(
    render: bool = typer.Option(False, "--render", help="Full render for each golden fixture"),
) -> None:
    """Replay golden fixtures and compare eval scores."""
    import yaml
    settings = get_settings()
    fixtures_dir = settings.root / "src" / "crewai_remotion" / "loops" / "fixtures" / "golden"
    if not fixtures_dir.exists():
        console.print("[red]No golden fixtures found[/red]")
        raise typer.Exit(1)

    for fixture_path in sorted(fixtures_dir.glob("*.yaml")):
        fixture = yaml.safe_load(fixture_path.read_text())
        console.print(f"\nFixture: {fixture_path.name}")
        console.print(f"  Topic: {fixture.get('topic', '?')}")
        console.print(f"  Brand: {fixture.get('brand', '?')}")
        floors = fixture.get("eval_floors", {})
        for metric, floor in floors.items():
            console.print(f"  {metric}: min {floor}")


@app.command()
def preview(
    run_id: Optional[str] = typer.Option(None, "--run", "-r", help="Run id under output/"),
    spec: Optional[Path] = typer.Option(None, "--spec", help="VideoSpec JSON for studio props"),
) -> None:
    """Open Remotion Studio (dev preview)."""
    import subprocess

    settings = get_settings()
    remotion_dir = settings.root / settings.remotion_project_path
    props_path = spec
    if run_id and not props_path:
        props_path = settings.output_dir / run_id / "render_props.json"
        if not props_path.exists():
            props_path = settings.output_dir / run_id / "video_spec.json"
    if props_path and props_path.exists():
        console.print(f"Studio props: {props_path}")
        console.print("In Remotion Studio, load this JSON as composition input props.")
    elif run_id:
        raise typer.BadParameter(f"No spec found for run: {run_id}")
    subprocess.run(["npm", "run", "studio"], cwd=remotion_dir)


def main() -> None:
    app()




@loop_app.command("distill")
def loop_distill(
    trace: Path = typer.Option(..., "--trace", help="trace.jsonl from a run"),
) -> None:
    from crewai_remotion.loops.flywheel import distill_from_trace

    result = distill_from_trace(trace)
    console.print_json(data=result)


if __name__ == "__main__":
    main()
