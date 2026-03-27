"""CLI formatters — convert data to Rich-compatible display formats."""
from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def format_risk_badge(risk_score: float) -> Text:
    """Format a risk score as a colored badge."""
    if risk_score >= 0.80:
        return Text(f" CRITICAL {risk_score:.2f} ", style="bold white on red")
    elif risk_score >= 0.60:
        return Text(f" HIGH {risk_score:.2f} ", style="bold white on dark_orange")
    elif risk_score >= 0.40:
        return Text(f" MEDIUM {risk_score:.2f} ", style="bold black on yellow")
    return Text(f" LOW {risk_score:.2f} ", style="bold white on green")


def format_tier_badge(tier: str) -> Text:
    """Format a tier as a colored badge."""
    colors = {
        "CRITICAL": "bold white on red",
        "HIGH": "bold white on dark_orange",
        "MEDIUM": "bold black on yellow",
        "LOW": "bold white on green",
    }
    style = colors.get(tier, "dim")
    return Text(f" {tier} ", style=style)


def format_signal_table(signals: list[dict[str, Any]], title: str = "Signals") -> Table:
    """Format signals as a Rich table."""
    table = Table(title=title, show_lines=False, padding=(0, 1))
    table.add_column("ID", style="dim", width=6)
    table.add_column("Tier", width=10)
    table.add_column("Risk", width=8, justify="right")
    table.add_column("Zone", width=16)
    table.add_column("Source", width=12)
    table.add_column("Title", max_width=40)

    for s in signals:
        tier = s.get("tier", "LOW")
        risk = s.get("risk_score", 0)

        table.add_row(
            str(s.get("id", "")),
            format_tier_badge(tier),
            f"{risk:.2f}" if risk else "—",
            s.get("geo_zone", "—") or "—",
            s.get("source", "—"),
            (s.get("title") or "—")[:40],
        )

    return table


def format_source_weights_table(weights: list[dict[str, Any]]) -> Table:
    """Format source weights as a Rich table."""
    table = Table(title="Source Weights", show_lines=False, padding=(0, 1))
    table.add_column("Source", width=20)
    table.add_column("Weight", width=10, justify="right")
    table.add_column("Last Calibrated", width=20)

    for w in weights:
        weight_val = w.get("weight", 0)
        style = "bold red" if weight_val < 0.3 else ("bold green" if weight_val > 0.7 else "")

        table.add_row(
            w.get("source", "—"),
            Text(f"{weight_val:.3f}", style=style),
            w.get("last_calibrated", "—") or "never",
        )

    return table


def format_status_panel(status: dict[str, Any]) -> Panel:
    """Format system status as a Rich panel."""
    lines: list[str] = []
    lines.append(f"Version: {status.get('version', '?')}")
    lines.append(f"Mode: {status.get('mode', '?')}")

    db_icon = "[green]OK[/]" if status.get("db_connected") else "[red]DOWN[/]"
    lines.append(f"PostgreSQL: {db_icon}")

    qdrant_icon = "[green]OK[/]" if status.get("qdrant_connected") else "[red]DOWN[/]"
    lines.append(f"Qdrant: {qdrant_icon}")

    lines.append(f"Signals: {status.get('signal_count', 0):,}")

    if "qdrant_points" in status:
        lines.append(f"Vectors: {status['qdrant_points']:,}")

    content = "\n".join(lines)
    return Panel(content, title="Noble Intel Status", border_style="blue")
