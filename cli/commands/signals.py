"""CLI command: signals — list and inspect signals."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from cli.formatters import format_signal_table

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def list_signals(
    ctx: typer.Context,
    tier: str = typer.Option(None, "--tier", "-t", help="Filter by tier"),
    zone: str = typer.Option(None, "--zone", "-z", help="Filter by geo zone"),
    risk: float = typer.Option(0.0, "--risk", "-r", help="Min risk score"),
    hours: int = typer.Option(24, "--hours", "-h", help="Last N hours"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """List intelligence signals."""
    remote = ctx.obj.get("remote", False) if ctx.obj else False

    if remote:
        from cli.remote.client import remote_get
        params = {}
        if tier:
            params["tier"] = tier
        if zone:
            params["geo_zone"] = zone
        if limit:
            params["limit"] = str(limit)
        data = remote_get("/cli/signals", params=params)
        signals = data.get("signals", [])
    else:
        from cli.db import get_local_signals
        signals = asyncio.run(
            get_local_signals(
                tier=tier,
                geo_zone=zone,
                min_risk=risk,
                last_hours=hours,
                limit=limit,
            )
        )

    if json_output:
        import json
        console.print_json(json.dumps(signals, indent=2, default=str))
    else:
        table = format_signal_table(signals, title=f"Signals (last {hours}h)")
        console.print(table)
        console.print(f"\n[dim]{len(signals)} signals shown[/dim]")
