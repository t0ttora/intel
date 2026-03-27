"""CLI command: sources — source weight management."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from cli.formatters import format_source_weights_table

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def list_sources(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """List all source weights."""
    remote = ctx.obj.get("remote", False) if ctx.obj else False

    if remote:
        from cli.remote.client import remote_get
        data = remote_get("/cli/sources")
        weights = data.get("sources", [])
    else:
        from cli.db import get_local_source_weights
        weights = asyncio.run(get_local_source_weights())

    if json_output:
        import json
        console.print_json(json.dumps(weights, indent=2, default=str))
    else:
        table = format_source_weights_table(weights)
        console.print(table)


@app.command("set")
def set_source_weight(
    source: str = typer.Argument(..., help="Source key"),
    weight: float = typer.Argument(..., help="New weight (0.1-1.0)"),
) -> None:
    """Manually set a source weight."""
    if weight < 0.1 or weight > 1.0:
        console.print("[red]Weight must be between 0.1 and 1.0[/red]")
        raise typer.Exit(1)

    async def _set():
        from app.db.pool import get_pool
        from app.db.queries import update_source_weight
        pool = await get_pool()
        async with pool.connection() as conn:
            await update_source_weight(conn, source, weight)
        return True

    asyncio.run(_set())
    console.print(f"[green]Set {source} weight to {weight:.3f}[/green]")
