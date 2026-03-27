"""CLI command: status — system health and stats."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from cli.formatters import format_status_panel

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Show system status and health."""
    remote = ctx.obj.get("remote", False) if ctx.obj else False

    if remote:
        from cli.remote.client import remote_get
        data = remote_get("/cli/status")
    else:
        from cli.db import get_local_status
        data = asyncio.run(get_local_status())

    if json_output:
        import json
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        panel = format_status_panel(data)
        console.print(panel)
