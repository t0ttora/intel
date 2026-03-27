"""CLI renderers — render complex intelligence results to the console."""
from __future__ import annotations

from typing import Any

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from cli.formatters import format_risk_badge, format_tier_badge


def render_query_result(result: dict[str, Any], console: Console) -> None:
    """Render a full intelligence query result."""
    # Header
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "LOW")
    grc = result.get("global_risk_composite", 0)
    confidence = result.get("confidence", 0)

    header = Panel(
        f"Risk: {format_risk_badge(risk_score)}  |  "
        f"GRC: {grc:.4f}  |  "
        f"Confidence: {confidence:.0%}",
        title=f"Intelligence Report — {risk_level}",
        border_style="red" if risk_score >= 0.60 else "yellow" if risk_score >= 0.40 else "green",
    )
    console.print(header)

    # Event summary
    summary = result.get("event_summary", "No data")
    console.print(Panel(summary, title="Event Summary", border_style="dim"))

    # Scenario
    scenario = result.get("scenario")
    if scenario:
        _render_scenario(scenario, console)

    # Cascade
    cascade = result.get("cascade")
    if cascade:
        _render_cascade(cascade, console)

    # User impact
    user_impact = result.get("user_impact")
    if user_impact:
        _render_user_impact(user_impact, console)

    # Data quality
    dq = result.get("data_quality", {})
    _render_data_quality(dq, console)

    # Sources
    sources = result.get("sources", [])
    if sources:
        _render_sources(sources, console)

    # TTL
    ttl = result.get("ttl_hours", 12)
    console.print(f"\n[dim]TTL: {ttl}h  |  Generated: {result.get('generated_at', '?')}[/dim]")


def _render_scenario(scenario: dict, console: Console) -> None:
    """Render scenario analysis."""
    table = Table(title="Scenario Analysis", show_lines=False, padding=(0, 1))
    table.add_column("Metric", width=20)
    table.add_column("p10", width=10, justify="right")
    table.add_column("p50", width=10, justify="right")
    table.add_column("p90", width=10, justify="right")

    delay = scenario.get("delay_distribution", {})
    cost = scenario.get("cost_distribution", {})

    table.add_row(
        "Delay",
        f"{delay.get('p10', 0):.1f}d",
        f"{delay.get('p50', 0):.1f}d",
        f"{delay.get('p90', 0):.1f}d",
    )
    table.add_row(
        "Cost Impact",
        f"${cost.get('p10', 0):,.0f}",
        f"${cost.get('p50', 0):,.0f}",
        f"${cost.get('p90', 0):,.0f}",
    )

    reroute_prob = scenario.get("reroute_probability", 0)
    console.print(table)
    console.print(f"  Reroute probability: {reroute_prob:.0%}")


def _render_cascade(cascade: dict, console: Console) -> None:
    """Render cascade propagation as a tree."""
    tree = Tree("Cascade Propagation")
    zones = cascade.get("affected_zones", [])
    depth = cascade.get("propagation_depth", 0)

    for zone in zones:
        tree.add(f"[yellow]{zone.replace('_', ' ').title()}[/yellow]")

    console.print(tree)
    console.print(f"  Depth: {depth}  |  {cascade.get('downstream_effects', '')}")


def _render_user_impact(impact: dict, console: Console) -> None:
    """Render user shipment impact."""
    table = Table(title="Your Shipment Impact", show_lines=False, padding=(0, 1))
    table.add_column("Code", width=12)
    table.add_column("Route", width=30)
    table.add_column("Status", width=12)
    table.add_column("Delay (p50)", width=12, justify="right")
    table.add_column("Cost (p50)", width=14, justify="right")

    for s in impact.get("affected_shipments", []):
        delay = s.get("estimated_delay", {})
        cost = s.get("cost_exposure", {})
        table.add_row(
            s.get("code", "—"),
            s.get("route", "—"),
            s.get("current_status", "—"),
            f"{delay.get('p50', '—')}d" if delay.get("p50") else "—",
            f"${cost.get('p50', 0):,.0f}" if cost.get("p50") else "—",
        )

    console.print(table)
    total = impact.get("total_exposure_usd", 0)
    console.print(f"  Total exposure: [bold]${total:,.0f}[/bold]  |  Priority: {impact.get('priority_score', 0):.2f}")


def _render_data_quality(dq: dict, console: Console) -> None:
    """Render data quality information."""
    level = dq.get("level", 0)
    level_labels = {0: "FULL", 1: "PARTIAL", 2: "HISTORICAL", 3: "RAG_OFFLINE", 4: "DEGRADED"}
    level_colors = {0: "green", 1: "yellow", 2: "dark_orange", 3: "red", 4: "bold red"}

    label = level_labels.get(level, "UNKNOWN")
    color = level_colors.get(level, "dim")

    parts = [
        f"[{color}]{label}[/{color}]",
        f"Signals: {dq.get('signal_count', 0)}",
        f"Sources: {dq.get('source_diversity', 0)}",
        f"Avg weight: {dq.get('avg_source_weight', 0):.3f}",
        f"Freshest: {dq.get('freshest_signal_age_hours', 0):.1f}h ago",
    ]

    degraded = dq.get("degraded_sources", [])
    if degraded:
        parts.append(f"[red]Degraded: {', '.join(degraded)}[/red]")

    console.print(Panel(" | ".join(parts), title="Data Quality", border_style="dim"))


def _render_sources(sources: list[dict], console: Console) -> None:
    """Render source list."""
    table = Table(title="Sources", show_lines=False, padding=(0, 1))
    table.add_column("Type", width=15)
    table.add_column("Weight", width=8, justify="right")
    table.add_column("URL", max_width=50)

    for s in sources[:5]:
        table.add_row(
            s.get("type", "—"),
            f"{s.get('weight', 0):.3f}",
            s.get("url", "—") or "—",
        )

    console.print(table)
