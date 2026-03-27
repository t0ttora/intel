"""TUI widgets — reusable Textual widgets for the dashboard."""
from __future__ import annotations

from textual.widgets import Static
from rich.text import Text


class RiskGauge(Static):
    """Visual risk score gauge widget."""

    def __init__(self, score: float = 0.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._score = score

    def set_score(self, score: float) -> None:
        self._score = max(0.0, min(1.0, score))
        self._render_gauge()

    def on_mount(self) -> None:
        self._render_gauge()

    def _render_gauge(self) -> None:
        bar_width = 30
        filled = int(self._score * bar_width)
        empty = bar_width - filled

        if self._score >= 0.80:
            color = "red"
            label = "CRITICAL"
        elif self._score >= 0.60:
            color = "dark_orange"
            label = "HIGH"
        elif self._score >= 0.40:
            color = "yellow"
            label = "MEDIUM"
        else:
            color = "green"
            label = "LOW"

        bar = f"[{color}]{'█' * filled}[/{color}]{'░' * empty}"
        self.update(f"{bar} {self._score:.2f} [{color}]{label}[/{color}]")


class MetricCard(Static):
    """Compact metric display widget."""

    def __init__(self, label: str = "", value: str = "0", **kwargs) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._value = value

    def set_value(self, value: str) -> None:
        self._value = value
        self._render()

    def on_mount(self) -> None:
        self._render()

    def _render(self) -> None:
        self.update(f"[dim]{self._label}[/dim]\n[bold]{self._value}[/bold]")


class ZoneIndicator(Static):
    """Geo zone status indicator."""

    ZONE_COLORS = {
        "CRITICAL": "red",
        "HIGH": "dark_orange",
        "MEDIUM": "yellow",
        "LOW": "green",
    }

    def update_zones(self, zones: list[dict]) -> None:
        """Update zone indicators.

        zones: list of {zone: str, risk_level: str, risk_score: float}
        """
        if not zones:
            self.update("[dim]No active zone alerts[/dim]")
            return

        lines: list[str] = []
        for z in zones[:8]:
            zone_name = z.get("zone", "?").replace("_", " ").title()
            level = z.get("risk_level", "LOW")
            score = z.get("risk_score", 0)
            color = self.ZONE_COLORS.get(level, "dim")
            lines.append(f"[{color}]●[/{color}] {zone_name}: {score:.2f}")

        self.update("\n".join(lines))
