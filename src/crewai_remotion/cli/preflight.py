from __future__ import annotations

import shutil
import sys

import typer
from rich.console import Console

from crewai_remotion.config import get_settings
from crewai_remotion.errors import ProductionError

console = Console()


def require_production_keys() -> None:
    settings = get_settings()
    if not settings.openai_api_key and not __import__("os").getenv("ANTHROPIC_API_KEY"):
        console.print("[bold red]Missing OPENAI_API_KEY (or ANTHROPIC_API_KEY)[/bold red]")
        console.print("Copy .env.example → .env and set keys before running create.")
        raise typer.Exit(1)
    if not settings.serper_api_key:
        console.print(
            "[yellow]Warning:[/yellow] SERPER_API_KEY is not set — topic/image research will be limited."
        )


def require_runtime_deps(*, need_render: bool = False) -> None:
    settings = get_settings()

    try:
        import crewai_remotion  # noqa: F401
    except ImportError as exc:
        raise ProductionError(
            "crewai-remotion package is not installed in this Python environment",
            phase="setup",
            hint="Run: uv pip install -e .  or use ./crewai-remotion from the project root",
        ) from exc

    if not shutil.which("node"):
        console.print("[yellow]Warning:[/yellow] node not found — Remotion render will use a placeholder.")

    if need_render:
        remotion_dir = settings.root / settings.remotion_project_path
        if not (remotion_dir / "package.json").exists():
            raise ProductionError(
                f"Remotion project not found at {remotion_dir}",
                phase="setup",
                hint="Run: cd remotion && npm install",
            )
        if not (remotion_dir / "node_modules").exists():
            console.print(
                "[yellow]Warning:[/yellow] remotion/node_modules missing — npm install will run during render."
            )


def ensure_cli_invocation() -> None:
    """Print a helpful hint when users run `crewai-remotion` without install/venv."""
    if shutil.which("crewai-remotion"):
        return
    if "crewai_remotion" in sys.modules:
        return
    console.print(
        "[dim]Tip: use ./crewai-remotion or source .venv/bin/activate[/dim]"
    )
