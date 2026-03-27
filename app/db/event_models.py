"""Pydantic models for the Event system (Decision Engine v1.0)."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Priority(str, enum.Enum):
    """Event priority levels based on impact score."""

    CRITICAL = "CRITICAL"  # > 80
    HIGH = "HIGH"  # 60-80
    MEDIUM = "MEDIUM"  # 40-60
    LOW = "LOW"  # < 40


class EventStatus(str, enum.Enum):
    """Event lifecycle status."""

    ACTIVE = "active"
    DECAYING = "decaying"
    RESOLVED = "resolved"


def classify_priority(impact_score: float) -> Priority:
    """Map a 0-100 impact score to a priority level."""
    if impact_score >= 80:
        return Priority.CRITICAL
    if impact_score >= 60:
        return Priority.HIGH
    if impact_score >= 40:
        return Priority.MEDIUM
    return Priority.LOW


# ── Core Schemas ──────────────────────────────────────────────────────────


class CascadeEffect(BaseModel):
    """A single predicted cascade effect."""

    zone: str
    description: str
    propagated_risk: float
    hop: int
    time_horizon_hours: str = Field(
        ..., description="e.g. '12-24h', '24-72h', '48-168h'"
    )


class EventDecision(BaseModel):
    """An actionable decision generated for an event."""

    decision: str = Field(..., description="Action text, e.g. 'Evaluate Cape reroute'")
    reason: str = Field(..., description="Why this decision was generated")
    urgency: str = Field(..., description="low / medium / high / critical")
    confidence: float = Field(..., ge=0, le=1)


class Event(BaseModel):
    """A fused event — a cluster of related signals elevated to a decision-grade entity."""

    event_id: UUID | None = None
    title: str
    summary: str
    impact_score: float = Field(..., ge=0, le=100)
    priority: Priority
    transport_modes: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0, le=1)
    signal_ids: list[UUID] = Field(default_factory=list)
    signal_count: int = 0
    source_diversity: int = 0
    decisions: list[EventDecision] = Field(default_factory=list)
    cascade_effects: list[CascadeEffect] = Field(default_factory=list)
    status: EventStatus = EventStatus.ACTIVE
    start_time: datetime | None = None
    updated_at: datetime | None = None
    expires_at: datetime | None = None


class EventCreate(BaseModel):
    """Input for persisting a new event."""

    title: str
    summary: str
    impact_score: float
    priority: str
    transport_modes: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    signal_ids: list[UUID] = Field(default_factory=list)
    signal_count: int = 0
    source_diversity: int = 0
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    cascade_effects: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "active"
    expires_at: datetime | None = None


# ── Clustering Intermediate ───────────────────────────────────────────────


class EventCluster(BaseModel):
    """Intermediate clustering result before scoring and decision generation."""

    signal_ids: list[UUID]
    titles: list[str]
    sources: list[str]
    transport_modes: list[str]
    regions: list[str]
    avg_risk_score: float
    max_risk_score: float
    earliest: datetime
    latest: datetime
