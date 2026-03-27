"""CLI command: risk — risk analysis and scoring."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.formatters import format_risk_badge

app = typer.Typer(no_args_is_help=False)
console = Console()


@app.command("score")
def risk_score(
    text: str = typer.Argument(..., help="Text to score for risk"),
    source: str = typer.Option("manual", "--source", "-s", help="Source key"),
) -> None:
    """Compute risk score for arbitrary text."""
    from app.scoring.risk_scorer import compute_risk_score, assign_tier
    from app.scoring.anomaly import compute_text_anomaly
    from app.scoring.geo_criticality import detect_geo_zone, get_geo_criticality
    from app.scoring.time_decay import compute_time_decay

    anomaly = compute_text_anomaly(text)
    geo_zone = detect_geo_zone(text)
    geo_crit = get_geo_criticality(geo_zone) if geo_zone else 0.3
    time_decay = compute_time_decay(0.0)  # Fresh

    score = compute_risk_score(
        anomaly_score=anomaly,
        source_weight=0.5,
        geo_criticality=geo_crit,
        time_decay_val=time_decay,
    )
    tier = assign_tier(score.risk_score, source)

    console.print(Panel(
        f"Risk: {format_risk_badge(score.risk_score)}\n"
        f"Tier: {tier}\n"
        f"Anomaly: {anomaly:.3f}\n"
        f"Geo Zone: {geo_zone or 'none detected'}\n"
        f"Geo Criticality: {geo_crit:.2f}\n"
        f"Time Decay: {time_decay:.3f}",
        title="Risk Analysis",
    ))


@app.command("cascade")
def risk_cascade(
    zone: str = typer.Argument(..., help="Source geo zone"),
    risk: float = typer.Argument(..., help="Initial risk score (0-1)"),
) -> None:
    """Simulate cascade propagation from a zone."""
    from app.engine.cascade import propagate_cascade

    result = propagate_cascade(zone, risk)

    if not result.affected_zones:
        console.print("[dim]No cascade propagation at this risk level.[/dim]")
        return

    table = Table(title=f"Cascade from {zone} (risk={risk:.2f})")
    table.add_column("Zone", width=20)
    table.add_column("Propagated Risk", width=16, justify="right")
    table.add_column("Hop", width=6, justify="right")

    for node in result.affected_zones:
        table.add_row(
            node.zone.replace("_", " ").title(),
            f"{node.propagated_risk:.3f}",
            str(node.hop),
        )

    console.print(table)
    console.print(f"\n[dim]Max depth: {result.max_depth_reached}[/dim]")


@app.command("grc")
def risk_grc(
    ctx: typer.Context,
) -> None:
    """Show current Global Risk Composite (GRC)."""
    remote = ctx.obj.get("remote", False) if ctx.obj else False

    if remote:
        from cli.remote.client import remote_get
        data = remote_get("/cli/status")
    else:
        from cli.db import get_local_status
        data = asyncio.run(get_local_status())

    stats = data.get("stats", {})
    console.print(Panel(
        f"Signal Count: {data.get('signal_count', 0):,}\n"
        f"Stats: {stats}",
        title="Global Risk Composite",
    ))


@app.command("scenario")
def risk_scenario(
    intent: str = typer.Argument("chokepoint", help="Intent type"),
    risk: float = typer.Argument(0.5, help="Risk score (0-1)"),
    geo_crit: float = typer.Option(0.8, "--geo", help="Geo criticality"),
    teu: int = typer.Option(1, "--teu", help="TEU count for cost estimation"),
) -> None:
    """Simulate a risk scenario."""
    from app.engine.scenarios import simulate_scenario, estimate_shipment_impact

    scenario = simulate_scenario(intent, risk, geo_crit)

    console.print(Panel(
        f"Reroute Probability: {scenario.reroute_probability:.0%}\n"
        f"Delay: p10={scenario.delay_distribution.p10:.1f}d "
        f"p50={scenario.delay_distribution.p50:.1f}d "
        f"p90={scenario.delay_distribution.p90:.1f}d\n"
        f"Cost: p10=${scenario.cost_distribution.p10:,.0f} "
        f"p50=${scenario.cost_distribution.p50:,.0f} "
        f"p90=${scenario.cost_distribution.p90:,.0f}",
        title=f"Scenario: {intent} (risk={risk:.2f})",
    ))

    if teu > 1:
        impact = estimate_shipment_impact(scenario, teu)
        console.print(f"\n  [bold]Shipment Impact ({teu} TEU):[/bold]")
        console.print(f"  Delay p50: {impact['delay_p50_days']:.1f} days")
        console.print(f"  Cost p50: ${impact['cost_p50_usd']:,.0f}")
