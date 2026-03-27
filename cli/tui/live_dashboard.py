"""Live TUI dashboard using Textual — real-time signal monitoring."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Static
from textual.timer import Timer

logger = logging.getLogger(__name__)


class SignalTable(DataTable):
    """Table showing latest signals."""

    def on_mount(self) -> None:
        self.add_columns("ID", "Tier", "Risk", "Zone", "Source", "Title")
        self.cursor_type = "row"


class AlertPanel(Static):
    """Panel showing active alerts."""

    def update_alerts(self, alerts: list[dict]) -> None:
        if not alerts:
            self.update("[dim]No active alerts[/dim]")
            return

        lines: list[str] = []
        for a in alerts[:5]:
            risk = a.get("risk_score", 0)
            title = (a.get("title") or "—")[:50]
            lines.append(f"[red]{risk:.2f}[/red] {title}")

        self.update("\n".join(lines))


class StatusBar(Static):
    """Top status bar with key metrics."""

    def update_status(self, data: dict) -> None:
        count = data.get("signal_count", 0)
        self.update(
            f"Signals: [bold]{count:,}[/bold]  |  "
            f"Last update: [dim]live[/dim]"
        )


class NobleDashboard(App):
    """Noble Intel Live Dashboard."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
    }

    #signal-table {
        column-span: 2;
        height: 1fr;
    }

    #alert-panel {
        height: auto;
        max-height: 12;
        border: solid $accent;
        padding: 1;
    }

    #status-bar {
        height: 3;
        border: solid $primary;
        padding: 0 1;
        column-span: 2;
    }

    #source-panel {
        height: auto;
        max-height: 12;
        border: solid $accent;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, refresh_interval: int = 5, remote: bool = False) -> None:
        super().__init__()
        self.refresh_interval = refresh_interval
        self.remote = remote
        self._timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(id="status-bar")
        yield SignalTable(id="signal-table")
        yield AlertPanel("Loading alerts...", id="alert-panel")
        yield Static("Loading sources...", id="source-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Noble Intel Dashboard"
        self._timer = self.set_interval(self.refresh_interval, self._refresh_data)
        # Initial load
        self.call_later(self._refresh_data)

    async def _refresh_data(self) -> None:
        """Fetch and update dashboard data."""
        try:
            if self.remote:
                data = await self._fetch_remote()
            else:
                data = await self._fetch_local()

            self._update_ui(data)
        except Exception as exc:
            logger.error(f"Dashboard refresh error: {exc}")

    async def _fetch_local(self) -> dict[str, Any]:
        """Fetch data locally."""
        from cli.db import get_local_status, get_local_signals, get_local_source_weights

        status = await get_local_status()
        signals = await get_local_signals(limit=15)
        weights = await get_local_source_weights()

        return {
            "signal_count": status.get("signal_count", 0),
            "latest_signals": signals,
            "active_alerts": [],
            "source_weights": weights,
        }

    async def _fetch_remote(self) -> dict[str, Any]:
        """Fetch data from remote API."""
        from cli.remote.client import async_remote_get

        status = await async_remote_get("/cli/status")
        signals = await async_remote_get("/cli/signals")
        sources = await async_remote_get("/cli/sources")

        return {
            "signal_count": status.get("signal_count", 0),
            "latest_signals": signals.get("signals", []),
            "active_alerts": [],
            "source_weights": sources.get("sources", []),
        }

    def _update_ui(self, data: dict[str, Any]) -> None:
        """Update all dashboard widgets with new data."""
        # Status bar
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_status(data)

        # Signal table
        table = self.query_one("#signal-table", SignalTable)
        table.clear()
        for s in data.get("latest_signals", [])[:15]:
            table.add_row(
                str(s.get("id", "")),
                s.get("tier", "—"),
                f"{s.get('risk_score', 0):.2f}" if s.get("risk_score") else "—",
                s.get("geo_zone", "—") or "—",
                s.get("source", "—"),
                (s.get("title") or "—")[:40],
            )

        # Alert panel
        alert_panel = self.query_one("#alert-panel", AlertPanel)
        alert_panel.update_alerts(data.get("active_alerts", []))

        # Source panel
        source_panel = self.query_one("#source-panel", Static)
        weights = data.get("source_weights", [])
        if weights:
            lines = [f"{w['source_key']}: {w['weight']:.3f}" for w in weights[:8]]
            source_panel.update("\n".join(lines))
        else:
            source_panel.update("[dim]No source data[/dim]")

    def action_refresh(self) -> None:
        """Manual refresh."""
        self.call_later(self._refresh_data)


def run_dashboard(refresh_interval: int = 5, remote: bool = False) -> None:
    """Launch the Textual live dashboard."""
    app = NobleDashboard(refresh_interval=refresh_interval, remote=remote)
    app.run()
