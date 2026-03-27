"""NobleCLI main entry point with local/remote mode detection."""
from __future__ import annotations

import os
import sys

import typer
from rich.console import Console

from cli.commands.status import app as status_app
from cli.commands.signals import app as signals_app
from cli.commands.risk import app as risk_app
from cli.commands.sources import app as sources_app
from cli.commands.qdrant_cmd import app as qdrant_app
from cli.commands.services import app as services_app
from cli.commands.pipeline import app as pipeline_app
from cli.commands.alerts import app as alerts_app
from cli.commands.calibration import app as calibration_app
from cli.commands.system import app as system_app

console = Console()

app = typer.Typer(
    name="noblecli",
    help="Noble Intel CLI — Adaptive Logistics Decision Engine",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-commands
app.add_typer(status_app, name="status", help="System status and health")
app.add_typer(signals_app, name="signals", help="Signal management")
app.add_typer(risk_app, name="risk", help="Risk analysis and scoring")
app.add_typer(sources_app, name="sources", help="Source weight management")
app.add_typer(qdrant_app, name="qdrant", help="Qdrant vector DB operations")
app.add_typer(services_app, name="services", help="Service management")
app.add_typer(pipeline_app, name="pipeline", help="Ingestion pipeline control")
app.add_typer(alerts_app, name="alerts", help="Alert management")
app.add_typer(calibration_app, name="calibrate", help="Calibration operations")
app.add_typer(system_app, name="system", help="System administration")


def is_remote_mode() -> bool:
    """Detect if CLI should run in remote mode (NOBLE_INTEL_URL is set)."""
    return bool(os.environ.get("NOBLE_INTEL_URL"))


@app.callback()
def main_callback(
    ctx: typer.Context,
    remote: bool = typer.Option(False, "--remote", "-r", help="Force remote mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Noble Intel CLI — local or remote mode."""
    ctx.ensure_object(dict)
    ctx.obj["remote"] = remote or is_remote_mode()
    ctx.obj["verbose"] = verbose

    if ctx.obj["verbose"]:
        mode = "REMOTE" if ctx.obj["remote"] else "LOCAL"
        console.print(f"[dim]Mode: {mode}[/dim]")


@app.command("query")
def query_command(
    query: str = typer.Argument(..., help="Intelligence query text"),
    geo_zone: str = typer.Option(None, "--zone", "-z", help="Geo zone filter"),
    cascade: bool = typer.Option(True, "--cascade/--no-cascade", help="Include cascade"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Run an intelligence query."""
    import asyncio

    if is_remote_mode():
        from cli.remote.client import remote_query
        result = remote_query(query, geo_zone=geo_zone, include_cascade=cascade)
    else:
        from cli.db import run_local_query
        result = asyncio.run(run_local_query(query, geo_zone=geo_zone, include_cascade=cascade))

    if json_output:
        import json
        console.print_json(json.dumps(result, indent=2, default=str))
    else:
        from cli.renderers import render_query_result
        render_query_result(result, console)


@app.command("dashboard")
def dashboard_command(
    refresh: int = typer.Option(5, "--refresh", "-r", help="Refresh interval (seconds)"),
) -> None:
    """Launch live TUI dashboard."""
    from cli.tui.live_dashboard import run_dashboard
    run_dashboard(refresh_interval=refresh, remote=is_remote_mode())


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
