"""Command line entry point.

Subcommands land as their specs do: `run` (005), `budget` (006), `sweep` (022),
`ingest` (019), `publish` (020). Day 1 ships `models` and `config`, which are
enough to inspect what the registry believes before anything is spent.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from harnesslab import __version__
from harnesslab.config import git_sha, settings
from harnesslab.providers import Lane, pooled_grid, registry

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="HarnessLab — does the scaffold matter more than the model?",
)
console = Console()


@app.command()
def version() -> None:
    """Print the version and the commit that is running."""
    sha = git_sha()
    console.print(f"harnesslab {__version__}" + (f"  ({sha[:8]})" if sha else ""))


@app.command()
def config() -> None:
    """Show resolved configuration. Never prints an API key -- it holds none."""
    s = settings()
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column(style="dim")
    table.add_column()
    table.add_row("log_dir", str(s.log_dir))
    table.add_row("data_dir", str(s.data_dir))
    table.add_row("results store", "postgres" if s.uses_postgres else "sqlite (local)")
    table.add_row("enforce_budget", "on" if s.enforce_budget else "OFF — overridden")
    table.add_row("git sha", git_sha() or "(not a git checkout)")
    console.print(table)


@app.command()
def models(
    lane: str | None = typer.Option(None, "--lane", help="Filter to lane A or B."),
    grid: bool = typer.Option(False, "--grid", help="Only the pooled primary grid."),
) -> None:
    """List known models with their free-tier capacity.

    The `traj/day` column is the number that actually matters. Raw quota figures
    mislead for agentic work: a trajectory is many calls that each resend
    accumulated history, so Groq's 70B reads as generous at 1,000 requests/day
    and is really about six trajectories.
    """
    specs = pooled_grid() if grid else sorted(registry().values(), key=lambda m: (m.lane, m.key))
    if lane:
        want = Lane(lane.upper())
        specs = [m for m in specs if m.lane is want]

    table = Table(title="Models" + (" — pooled primary grid" if grid else ""))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("lane", justify="center")
    table.add_column("model string", style="dim", no_wrap=True)
    table.add_column("ctx cap", justify="right")
    table.add_column("traj/day", justify="right")
    table.add_column("binds on", justify="center")
    table.add_column("gate", justify="center")

    for m in specs:
        per_day = m.limits.trajectories_per_day()
        gate = {
            "passed": "[green]pass[/]",
            "pending": "[yellow]pending[/]",
            "rejected": "[red]rejected[/]",
        }[m.gate.value]
        ceiling = m.limits.context_ceiling
        table.add_row(
            m.key,
            m.lane.value,
            m.inspect_model,
            f"{ceiling:,}" if ceiling else "-",
            # Plain ASCII: the Windows console is cp1252 and cannot encode the
            # infinity sign, which crashes rich mid-render.
            "no cap" if per_day is None else f"{per_day:,}",
            m.limits.binds_on(),
            gate if m.lane is Lane.LOCAL else "—",
        )
    console.print(table)

    pending = [m.key for m in pooled_grid() if not m.sweep_ready]
    if pending:
        console.print(
            f"\n[yellow]{len(pending)} pooled model(s) awaiting the Lane A gate "
            f"(SPEC-010, day 8):[/] {', '.join(pending)}\n"
            "[dim]No scored sweep may run until each is pinned by digest.[/]"
        )


if __name__ == "__main__":
    app()
