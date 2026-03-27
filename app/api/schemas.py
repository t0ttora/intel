"""Pydantic request/response schemas for the Intel API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """POST /query request body."""

    query: str = Field(..., min_length=3, max_length=500, description="Intelligence query text")
    geo_zone: str | None = Field(None, description="Specific geo zone to focus on")
    min_risk_score: float | None = Field(None, ge=0, le=1, description="Minimum risk score filter")
    include_cascade: bool = Field(True, description="Include cascade propagation analysis")
    include_user_impact: bool = Field(False, description="Include user shipment impact analysis")
    user_id: str | None = Field(None, description="User ID for shipment impact (required if include_user_impact)")


class SignalsRequest(BaseModel):
    """GET /signals query parameters."""

    tier: str | None = Field(None, description="Filter by tier: CRITICAL, HIGH, MEDIUM, LOW")
    geo_zone: str | None = Field(None, description="Filter by geo zone")
    min_risk_score: float | None = Field(None, ge=0, le=1, description="Minimum risk score")
    last_hours: int = Field(24, ge=1, le=168, description="Signals from last N hours")
    limit: int = Field(50, ge=1, le=200, description="Max signals to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


# ── Response Schemas ──────────────────────────────────────────────────────


class DataQuality(BaseModel):
    """Data quality block in intelligence response."""

    level: int = Field(..., description="Degradation level 0-4")
    signal_count: int
    source_diversity: int
    avg_source_weight: float
    freshest_signal_age_hours: float
    degraded_sources: list[str] = Field(default_factory=list)
    fallback_mode: str | None = None
    confidence_drop_reason: str | None = None


class DistributionResponse(BaseModel):
    """p10/p50/p90 distribution."""

    p10: float
    p50: float
    p90: float
    unit: str


class ScenarioResponse(BaseModel):
    """Scenario simulation results."""

    reroute_probability: float
    delay_distribution: DistributionResponse
    cost_distribution: DistributionResponse


class CascadeResponse(BaseModel):
    """Cascade propagation results."""

    propagation_depth: int
    affected_zones: list[str]
    downstream_effects: str


class ShipmentImpact(BaseModel):
    """Individual shipment impact."""

    code: str
    route: str
    current_status: str
    delay_probability: float | None = None
    estimated_delay: dict[str, Any] | None = None
    cost_exposure: dict[str, Any] | None = None


class UserImpact(BaseModel):
    """User impact block."""

    affected_shipments: list[ShipmentImpact]
    total_exposure_usd: float
    priority_score: float


class SourceEntry(BaseModel):
    """Source entry in response."""

    type: str
    weight: float
    url: str | None = None


class IntelligenceResponse(BaseModel):
    """Full intelligence response from POST /query."""

    risk_level: str
    risk_score: float
    global_risk_composite: float
    event_summary: str
    confidence: float
    data_quality: DataQuality
    generated_at: str
    ttl_hours: int
    scenario: ScenarioResponse | None = None
    cascade: CascadeResponse | None = None
    user_impact: UserImpact | None = None
    sources: list[SourceEntry] = Field(default_factory=list)


class SignalResponse(BaseModel):
    """Single signal in signals list response."""

    id: int
    title: str | None = None
    content: str
    source: str
    url: str | None = None
    geo_zone: str | None = None
    risk_score: float | None = None
    tier: str | None = None
    created_at: datetime


class SignalsListResponse(BaseModel):
    """GET /signals response."""

    signals: list[SignalResponse]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    """GET /health response."""

    status: str
    version: str = "3.0.0"
    db_connected: bool
    qdrant_connected: bool
    signal_count: int
    uptime_seconds: float
