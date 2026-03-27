"""CLI command: pipeline — manual ingestion pipeline control."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command("rss")
def run_rss(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without ingesting"),
) -> None:
    """Manually trigger RSS ingestion."""
    if dry_run:
        from app.ingestion.rss import RSS_FEEDS
        console.print(f"[dim]Would ingest from {len(RSS_FEEDS)} feeds:[/dim]")
        for feed in RSS_FEEDS:
            console.print(f"  - {feed['source']}: {feed['url']}")
        return

    console.print("[yellow]Running RSS ingestion...[/yellow]")

    async def _run():
        from app.tasks.ingest_rss import _ingest_rss
        return await _ingest_rss()

    stats = asyncio.run(_run())
    console.print(Panel(
        f"Fetched: {stats.get('fetched', 0)}\n"
        f"Filtered: {stats.get('filtered', 0)}\n"
        f"Duplicated: {stats.get('duplicated', 0)}\n"
        f"Injected: {stats.get('injected', 0)}\n"
        f"Ingested: {stats.get('ingested', 0)}\n"
        f"Errors: {stats.get('errors', 0)}",
        title="RSS Ingestion Result",
        border_style="green" if stats.get("errors", 0) == 0 else "red",
    ))


@app.command("scrape")
def run_scraper(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without scraping"),
) -> None:
    """Manually trigger web scraper."""
    if dry_run:
        console.print("[dim]Would scrape: Reddit (3 subs), Playwright targets[/dim]")
        return

    console.print("[yellow]Running scraper ingestion...[/yellow]")

    async def _run():
        from app.tasks.ingest_scraper import _ingest_scraper
        return await _ingest_scraper()

    stats = asyncio.run(_run())
    console.print(Panel(
        f"Fetched: {stats.get('fetched', 0)}\n"
        f"Filtered: {stats.get('filtered', 0)}\n"
        f"Duplicated: {stats.get('duplicated', 0)}\n"
        f"Ingested: {stats.get('ingested', 0)}\n"
        f"Errors: {stats.get('errors', 0)}",
        title="Scraper Ingestion Result",
        border_style="green" if stats.get("errors", 0) == 0 else "red",
    ))


@app.command("full")
def run_full_pipeline() -> None:
    """Run the full ingestion pipeline (RSS + scraper)."""
    console.print("[yellow]Running full pipeline...[/yellow]")

    async def _run():
        from app.tasks.ingest_rss import _ingest_rss
        from app.tasks.ingest_scraper import _ingest_scraper

        rss_stats = await _ingest_rss()
        scraper_stats = await _ingest_scraper()
        return {"rss": rss_stats, "scraper": scraper_stats}

    results = asyncio.run(_run())

    rss = results.get("rss", {})
    scraper = results.get("scraper", {})
    total_ingested = rss.get("ingested", 0) + scraper.get("ingested", 0)
    total_errors = rss.get("errors", 0) + scraper.get("errors", 0)

    console.print(f"\n[green]Total ingested: {total_ingested}[/green]")
    if total_errors:
        console.print(f"[red]Total errors: {total_errors}[/red]")
