"""CLI command: qdrant — Qdrant vector DB operations."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command("info")
def qdrant_info() -> None:
    """Show Qdrant collection info."""

    async def _info():
        from app.config import get_settings
        from app.vectordb.client import get_qdrant_client, get_collection_info

        settings = get_settings()
        qdrant = get_qdrant_client()
        return await get_collection_info(qdrant, settings.qdrant_collection)

    info = asyncio.run(_info())

    if info:
        console.print(Panel(
            f"Collection: {info.get('name', '?')}\n"
            f"Points: {info.get('points_count', 0):,}\n"
            f"Vectors: {info.get('vectors_count', 0):,}\n"
            f"Segments: {info.get('segments_count', 0)}",
            title="Qdrant Collection Info",
        ))
    else:
        console.print("[red]Could not connect to Qdrant[/red]")


@app.command("search")
def qdrant_search(
    query: str = typer.Argument(..., help="Search query text"),
    zone: str = typer.Option(None, "--zone", "-z", help="Filter by geo zone"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results"),
) -> None:
    """Semantic search in Qdrant."""

    async def _search():
        from app.config import get_settings
        from app.vectordb.client import get_qdrant_client
        from app.vectordb.search import semantic_search

        settings = get_settings()
        qdrant = get_qdrant_client()
        return await semantic_search(
            qdrant,
            settings.qdrant_collection,
            query,
            limit=limit,
            geo_zone=zone,
        )

    results = asyncio.run(_search())

    table = Table(title=f"Qdrant Search: '{query}'")
    table.add_column("Score", width=8, justify="right")
    table.add_column("Signal ID", width=10)
    table.add_column("Source", width=12)
    table.add_column("Zone", width=16)
    table.add_column("Risk", width=8, justify="right")

    for r in results:
        payload = r.get("payload", {})
        table.add_row(
            f"{r.get('score', 0):.4f}",
            str(payload.get("signal_id", "—")),
            payload.get("source", "—"),
            payload.get("geo_zone", "—"),
            f"{payload.get('risk_score', 0):.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]{len(results)} results[/dim]")


@app.command("stats")
def qdrant_stats() -> None:
    """Show Qdrant collection statistics."""

    async def _stats():
        from app.config import get_settings
        from app.vectordb.client import get_qdrant_client, get_collection_info

        settings = get_settings()
        qdrant = get_qdrant_client()
        return await get_collection_info(qdrant, settings.qdrant_collection)

    info = asyncio.run(_stats())

    if info:
        console.print(f"Points: {info.get('points_count', 0):,}")
        console.print(f"Vectors: {info.get('vectors_count', 0):,}")
        console.print(f"Segments: {info.get('segments_count', 0)}")
    else:
        console.print("[red]Qdrant unavailable[/red]")
