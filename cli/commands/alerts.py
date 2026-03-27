"""CLI command: alerts — alert management."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from cli.formatters import format_risk_badge

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def list_alerts(
    ctx: typer.Context,
    active_only: bool = typer.Option(True, "--active/--all", help="Show active alerts only"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """List alerts."""

    async def _get():
        from app.db.pool import get_pool
        from app.db.queries import get_active_alerts, get_alerts
        pool = await get_pool()
        async with pool.connection() as conn:
            if active_only:
                return await get_active_alerts(conn, limit=limit)
            return await get_alerts(conn, limit=limit)

    alerts = asyncio.run(_get())

    if json_output:
        import json
        data = [
            {
                "id": a.id,
                "title": a.title,
                "risk_score": a.risk_score,
                "alert_type": a.alert_type,
                "geo_zone": a.geo_zone,
                "pushed_at": a.pushed_at.isoformat() if a.pushed_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
        console.print_json(json.dumps(data, indent=2, default=str))
        return

    table = Table(title="Alerts")
    table.add_column("ID", width=6)
    table.add_column("Type", width=10)
    table.add_column("Risk", width=8, justify="right")
    table.add_column("Zone", width=16)
    table.add_column("Title", max_width=40)
    table.add_column("Pushed", width=8)

    for a in alerts:
        pushed = "[green]Yes[/green]" if a.pushed_at else "[dim]No[/dim]"
        table.add_row(
            str(a.id),
            a.alert_type or "—",
            f"{a.risk_score:.2f}" if a.risk_score else "—",
            a.geo_zone or "—",
            (a.title or "—")[:40],
            pushed,
        )

    console.print(table)
    console.print(f"\n[dim]{len(alerts)} alerts shown[/dim]")


@app.command("push")
def push_alerts() -> None:
    """Manually check and push critical alerts."""
    console.print("[yellow]Checking for critical signals...[/yellow]")

    async def _push():
        from app.db.pool import get_pool
        from app.alerts.pusher import check_and_push_alerts
        pool = await get_pool()
        async with pool.connection() as conn:
            return await check_and_push_alerts(conn)

    alerts = asyncio.run(_push())
    console.print(f"[green]Pushed {len(alerts)} alerts to Supabase[/green]")
