"""Pydantic models matching PostgreSQL tables."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Signal(BaseModel):
    """A single ingested signal."""

    id: UUID
    source: str
    tier: str
    source_type: str | None = None  # news, official, social, physical, pricing
    geo_zone: str | None = None
    title: str | None = None
    content: str
    url: str | None = None
    risk_score: float | None = None
    anomaly_score: float | None = None
    source_weight: float | None = None
    geo_criticality: float | None = None
    time_decay: float | None = None
    reliability_score: float | None = None
    embedding_id: str | None = None
    transport_mode: str | None = None
    region: str | None = None
    created_at: datetime
    expires_at: datetime | None = None


class SignalCreate(BaseModel):
    """Input for creating a new signal."""

    source: str
    tier: str
    source_type: str | None = None  # news, official, social, physical, pricing
    geo_zone: str | None = None
    title: str | None = None
    content: str
    url: str | None = None
    risk_score: float | None = None
    anomaly_score: float | None = None
    source_weight: float | None = None
    geo_criticality: float | None = None
    time_decay: float | None = None
    reliability_score: float | None = None
    embedding_id: str | None = None
    content_hash: str | None = None
    transport_mode: str | None = None
    region: str | None = None
    expires_at: datetime | None = None


class SourceWeight(BaseModel):
    """Source calibration state."""

    source: str
    current_weight: float
    base_weight: float
    floor_weight: float
    ceiling_weight: float
    total_signals: int = 0
    total_accurate: int = 0
    last_calibrated_at: datetime


class Alert(BaseModel):
    """Alert pushed to Supabase."""

    id: UUID
    signal_id: UUID | None = None
    risk_level: str
    risk_score: float
    cascade_data: dict[str, Any] | None = None
    pushed_to_supabase: bool = False
    pushed_at: datetime | None = None
    created_at: datetime


class AlertCreate(BaseModel):
    """Input for creating an alert."""

    signal_id: UUID | None = None
    risk_level: str
    risk_score: float
    cascade_data: dict[str, Any] | None = None


class Outcome(BaseModel):
    """Signal-event-outcome tracking."""

    id: UUID
    signal_id: UUID | None = None
    predicted_impact: str | None = None
    actual_outcome: str | None = None
    accuracy_score: float | None = None
    lead_time_hours: float | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class OutcomeCreate(BaseModel):
    """Input for recording an outcome."""

    signal_id: UUID
    predicted_impact: str | None = None
    actual_outcome: str | None = None
    accuracy_score: float | None = None
    lead_time_hours: float | None = None
