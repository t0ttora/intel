"""CLI command: services — manage systemd services."""
from __future__ import annotations

import subprocess

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=False)
console = Console()

SERVICES = [
    "noble-intel",
    "noble-intel-worker",
    "noble-intel-beat",
]


def _run_systemctl(action: str, service: str) -> tuple[bool, str]:
    """Run a systemctl command."""
    try:
        result = subprocess.run(
            ["systemctl", action, service],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "systemctl not found (not on systemd host?)"


@app.callback(invoke_without_command=True)
def services_status(ctx: typer.Context) -> None:
    """Show status of all Noble Intel services."""
    table = Table(title="Service Status")
    table.add_column("Service", width=24)
    table.add_column("Status", width=12)
    table.add_column("Details", max_width=40)

    for service in SERVICES:
        ok, output = _run_systemctl("is-active", service)
        status = "[green]active[/green]" if ok else "[red]inactive[/red]"
        table.add_row(service, status, output[:40])

    console.print(table)


@app.command("start")
def start_service(
    service: str = typer.Argument(None, help="Service name (omit for all)"),
) -> None:
    """Start a service (or all services)."""
    targets = [service] if service else SERVICES
    for svc in targets:
        ok, output = _run_systemctl("start", svc)
        icon = "[green]Started[/green]" if ok else "[red]Failed[/red]"
        console.print(f"{icon} {svc}: {output}")


@app.command("stop")
def stop_service(
    service: str = typer.Argument(None, help="Service name (omit for all)"),
) -> None:
    """Stop a service (or all services)."""
    targets = [service] if service else SERVICES
    for svc in targets:
        ok, output = _run_systemctl("stop", svc)
        icon = "[yellow]Stopped[/yellow]" if ok else "[red]Failed[/red]"
        console.print(f"{icon} {svc}: {output}")


@app.command("restart")
def restart_service(
    service: str = typer.Argument(None, help="Service name (omit for all)"),
) -> None:
    """Restart a service (or all services)."""
    targets = [service] if service else SERVICES
    for svc in targets:
        ok, output = _run_systemctl("restart", svc)
        icon = "[green]Restarted[/green]" if ok else "[red]Failed[/red]"
        console.print(f"{icon} {svc}: {output}")


@app.command("logs")
def service_logs(
    service: str = typer.Argument("noble-intel", help="Service name"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """Show service logs via journalctl."""
    cmd = ["journalctl", "-u", service, "-n", str(lines), "--no-pager"]
    if follow:
        cmd.append("-f")

    try:
        result = subprocess.run(cmd, capture_output=not follow, text=True, timeout=30 if not follow else None)
        if not follow:
            console.print(result.stdout)
    except subprocess.TimeoutExpired:
        console.print("[dim]Log output timed out[/dim]")
    except FileNotFoundError:
        console.print("[red]journalctl not found[/red]")
