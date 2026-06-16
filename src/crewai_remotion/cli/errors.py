from __future__ import annotations

import traceback

import typer
from rich.console import Console

from crewai_remotion.errors import ProductionError

console = Console()


def report_error(exc: BaseException, *, verbose: bool = False) -> None:
  if isinstance(exc, typer.Exit):
    raise exc

  if isinstance(exc, ProductionError):
    console.print("\n[bold red]✗ Production failed[/bold red]")
    console.print(f"  {exc.message}")
    if exc.phase:
      console.print(f"  Phase: [cyan]{exc.phase}[/cyan]")
    if exc.run_dir:
      console.print(f"  Run output: [dim]{exc.run_dir}[/dim]")
    if exc.hint:
      console.print(f"\n  [yellow]Hint:[/yellow] {exc.hint}")
    if verbose and exc.__cause__:
      console.print(f"\n[dim]Cause: {exc.__cause__}[/dim]")
    raise typer.Exit(1) from None

  console.print("\n[bold red]✗ Unexpected error[/bold red]")
  console.print(f"  {exc}")
  if verbose:
    console.print("\n[dim]" + traceback.format_exc() + "[/dim]")
  else:
    console.print("  Re-run with [bold]--verbose[/bold] for a full traceback.")
  raise typer.Exit(1) from None
