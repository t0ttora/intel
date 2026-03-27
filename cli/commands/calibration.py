"""CLI command: calibrate — manual calibration operations."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command("sources")
def calibrate_sources() -> None:
    """Run source weight calibration."""
    console.print("[yellow]Running source weight calibration...[/yellow]")

    async def _run():
        from app.db.pool import get_pool
        from app.calibration.source_weights import calibrate_all_sources
        pool = await get_pool()
        async with pool.connection() as conn:
            return await calibrate_all_sources(conn)

    results = asyncio.run(_run())
    console.print(Panel(
        "\n".join(f"{k}: {v}" for k, v in results.items()),
        title="Source Calibration Results",
        border_style="green",
    ))


@app.command("formula")
def calibrate_formula() -> None:
    """Run formula weight recalibration (Pearson correlation)."""
    console.print("[yellow]Running formula weight recalibration...[/yellow]")

    async def _run():
        from app.db.pool import get_pool
        from app.calibration.formula_weights import recalibrate_formula
        pool = await get_pool()
        async with pool.connection() as conn:
            return await recalibrate_formula(conn)

    result = asyncio.run(_run())
    console.print(Panel(
        "\n".join(f"{k}: {v}" for k, v in result.items()),
        title="Formula Calibration Results",
        border_style="green",
    ))


@app.command("cascade")
def calibrate_cascade() -> None:
    """Run cascade edge weight calibration."""
    console.print("[yellow]Running cascade edge calibration...[/yellow]")

    async def _run():
        from app.db.pool import get_pool
        from app.calibration.cascade_edges import calibrate_cascade_edges
        pool = await get_pool()
        async with pool.connection() as conn:
            return await calibrate_cascade_edges(conn)

    result = asyncio.run(_run())
    console.print(Panel(
        "\n".join(f"{k}: {v}" for k, v in result.items()),
        title="Cascade Calibration Results",
        border_style="green",
    ))


@app.command("drift")
def check_drift() -> None:
    """Check for weight drift from baselines."""

    async def _run():
        from app.db.pool import get_pool
        from app.calibration.drift_detector import detect_drifts
        pool = await get_pool()
        async with pool.connection() as conn:
            return await detect_drifts(conn)

    drifts = asyncio.run(_run())

    if not drifts:
        console.print("[green]No drift detected. All weights within normal range.[/green]")
        return

    table = Table(title="Drift Alerts")
    table.add_column("Source", width=20)
    table.add_column("Current", width=10, justify="right")
    table.add_column("Baseline", width=10, justify="right")
    table.add_column("Delta", width=10, justify="right")
    table.add_column("Severity", width=12)

    for d in drifts:
        severity_style = "bold red" if d.severity == "HIGH" else "yellow"
        table.add_row(
            d.source_key,
            f"{d.current_weight:.3f}",
            f"{d.baseline_weight:.3f}",
            f"{d.delta:.3f}",
            f"[{severity_style}]{d.severity}[/{severity_style}]",
        )

    console.print(table)


@app.command("all")
def calibrate_all() -> None:
    """Run all calibration tasks."""
    calibrate_sources()
    calibrate_formula()
    calibrate_cascade()
    check_drift()
