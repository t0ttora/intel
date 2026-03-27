"""CLI command: system — system administration."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command("cleanup")
def system_cleanup(
    days: int = typer.Option(30, "--days", "-d", help="Retention period in days"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without deleting"),
) -> None:
    """Clean up expired signals."""
    if dry_run:
        async def _count():
            from app.db.pool import get_pool
            pool = await get_pool()
            async with pool.connection() as conn:
                from app.db.queries import get_signal_count
                total = await get_signal_count(conn)
            return total

        total = asyncio.run(_count())
        console.print(f"[dim]Would clean signals older than {days} days (current total: {total:,})[/dim]")
        return

    console.print(f"[yellow]Cleaning signals older than {days} days...[/yellow]")

    async def _cleanup():
        from app.db.pool import get_pool
        from app.db.queries import expire_old_signals
        pool = await get_pool()
        async with pool.connection() as conn:
            return await expire_old_signals(conn, days=days)

    deleted = asyncio.run(_cleanup())
    console.print(f"[green]Deleted {deleted:,} expired signals[/green]")


@app.command("info")
def system_info() -> None:
    """Show system information."""
    import platform
    import sys

    console.print(Panel(
        f"Python: {sys.version}\n"
        f"Platform: {platform.platform()}\n"
        f"Architecture: {platform.machine()}\n"
        f"Node: {platform.node()}",
        title="System Info",
    ))


@app.command("config")
def system_config(
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show secret values"),
) -> None:
    """Show current configuration."""
    from app.config import get_settings

    settings = get_settings()

    lines = [
        f"QDRANT_HOST: {settings.qdrant_host}",
        f"QDRANT_PORT: {settings.qdrant_port}",
        f"QDRANT_COLLECTION: {settings.qdrant_collection}",
        f"DATABASE_URL: {'***' if not show_secrets else settings.database_url}",
        f"REDIS_URL: {settings.redis_url}",
        f"SUPABASE_URL: {settings.supabase_url}",
        f"GEMINI_API_KEY: {'***' if not show_secrets else settings.gemini_api_key}",
        f"INTEL_API_KEY: {'***' if not show_secrets else settings.intel_api_key}",
        f"SENTRY_DSN: {'***' if not show_secrets else (settings.sentry_dsn or 'not set')}",
        f"DEBUG: {settings.debug}",
    ]

    console.print(Panel("\n".join(lines), title="Configuration", border_style="blue"))


@app.command("health")
def system_health() -> None:
    """Run a comprehensive health check."""
    console.print("[yellow]Running health check...[/yellow]")

    async def _check():
        from app.db.pool import get_pool
        from app.config import get_settings
        from app.vectordb.client import get_qdrant_client, get_collection_info

        results = {"db": False, "qdrant": False, "redis": False}

        # Check PostgreSQL
        try:
            pool = await get_pool()
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
            results["db"] = True
        except Exception:
            pass

        # Check Qdrant
        try:
            settings = get_settings()
            qdrant = get_qdrant_client()
            info = await get_collection_info(qdrant, settings.qdrant_collection)
            results["qdrant"] = info is not None
        except Exception:
            pass

        # Check Redis
        try:
            import redis as redis_lib
            settings = get_settings()
            r = redis_lib.from_url(settings.redis_url)
            r.ping()
            results["redis"] = True
        except Exception:
            pass

        return results

    results = asyncio.run(_check())

    for service, ok in results.items():
        icon = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        console.print(f"  {service}: {icon}")

    all_ok = all(results.values())
    if all_ok:
        console.print("\n[green bold]All systems operational[/green bold]")
    else:
        console.print("\n[red bold]Some systems are down[/red bold]")
        raise typer.Exit(1)
