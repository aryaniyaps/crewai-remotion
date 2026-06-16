from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from crewai_remotion.cli.brand_wizard import run_brand_wizard
from crewai_remotion.config import get_settings
from crewai_remotion.models.brand import BrandProfile, load_brand

console = Console()


def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _find_brand_files(root: Path) -> list[Path]:
    brands = root / "brands"
    if not brands.exists():
        return []
    return sorted(brands.glob("**/*.brand.yaml"))


def resolve_brand(
    brand_path: str | None,
    *,
    non_interactive: bool = False,
    inline_wizard: bool = True,
) -> tuple[BrandProfile, Path]:
    settings = get_settings()
    root = settings.root

    if brand_path:
        path = Path(brand_path)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return load_brand(path), path
        if non_interactive:
            raise typer.BadParameter(f"Brand file not found: {path}")
        if not _is_tty():
            raise typer.BadParameter(f"Brand file not found: {path}. Use --non-interactive only with valid --brand.")
        console.print(f"[yellow]Brand file not found at {path} — starting wizard[/yellow]")
        slug_hint = path.stem.replace(".brand", "")
        profile, saved = run_brand_wizard(slug_hint=slug_hint, inline=inline_wizard)
        return profile, saved

    active_file = settings.brands_dir / ".active"
    if active_file.exists():
        rel = active_file.read_text(encoding="utf-8").strip()
        path = root / rel
        if path.exists():
            return load_brand(path), path

    files = _find_brand_files(root)
    if len(files) == 1:
        return load_brand(files[0]), files[0]

    if non_interactive:
        raise typer.BadParameter("No brand profile found. Pass --brand or run interactively.")

    if not _is_tty():
        raise typer.BadParameter("No brand profile and non-TTY environment. Pass --brand.")

    console.print("[bold yellow]No brand profile found.[/bold yellow]")
    profile, saved = run_brand_wizard(inline=inline_wizard)
    return profile, saved


def set_active_brand(path: Path) -> None:
    settings = get_settings()
    rel = path.relative_to(settings.root)
    active = settings.brands_dir / ".active"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(str(rel), encoding="utf-8")
