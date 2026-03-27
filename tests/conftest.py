"""Shared test fixtures for Noble Intel."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models import Signal, SignalCreate, SourceWeight, Alert


# ── Environment ───────────────────────────────────────────────────────────

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/intel_test")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6333")
os.environ.setdefault("QDRANT_COLLECTION", "intel_signals_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")
os.environ.setdefault("INTEL_API_KEY", "test-api-key")


# ── Signal Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def sample_signal() -> Signal:
    """A sample signal for testing."""
    return Signal(
        id=1,
        title="Suez Canal blockage causes major delays",
        content="A container vessel has run aground in the Suez Canal, blocking "
        "all transit traffic. Port congestion is expected to worsen in "
        "Rotterdam and Hamburg within 48 hours.",
        source="reuters_maritime",
        url="https://example.com/suez-blockage",
        content_hash="abc123def456",
        geo_zone="suez_canal",
        risk_score=0.85,
        anomaly_score=0.75,
        source_weight=0.70,
        geo_criticality=0.95,
        time_decay=0.98,
        tier="CRITICAL",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_signals() -> list[Signal]:
    """A list of sample signals across different zones."""
    now = datetime.now(timezone.utc)
    return [
        Signal(
            id=1, title="Suez blockage", content="Major blockage at Suez",
            source="reuters_maritime", geo_zone="suez_canal",
            risk_score=0.85, anomaly_score=0.75, source_weight=0.70,
            geo_criticality=0.95, time_decay=0.98, tier="CRITICAL",
            created_at=now,
        ),
        Signal(
            id=2, title="Panama drought", content="Water levels critical at Panama",
            source="freightwaves", geo_zone="panama_canal",
            risk_score=0.70, anomaly_score=0.60, source_weight=0.65,
            geo_criticality=0.90, time_decay=0.95, tier="HIGH",
            created_at=now,
        ),
        Signal(
            id=3, title="Port congestion Shanghai", content="Dwell times rising at Shanghai",
            source="splash247", geo_zone="shanghai",
            risk_score=0.45, anomaly_score=0.40, source_weight=0.50,
            geo_criticality=0.85, time_decay=0.90, tier="MEDIUM",
            created_at=now,
        ),
    ]


@pytest.fixture
def sample_signal_create() -> SignalCreate:
    """A sample SignalCreate for insert testing."""
    return SignalCreate(
        title="Test signal",
        content="Port of Rotterdam experiencing heavy congestion due to storm damage",
        source="test_source",
        url="https://example.com/test",
        content_hash="hash_123",
        geo_zone="rotterdam",
        risk_score=0.55,
        anomaly_score=0.40,
        source_weight=0.60,
        geo_criticality=0.80,
        time_decay=0.92,
        tier="MEDIUM",
    )


@pytest.fixture
def sample_source_weight() -> SourceWeight:
    """A sample source weight."""
    return SourceWeight(
        id=1,
        source_key="reuters_maritime",
        weight=0.70,
        last_calibrated=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_alert() -> Alert:
    """A sample alert."""
    return Alert(
        id=1,
        signal_id=1,
        alert_type="CRITICAL",
        risk_score=0.85,
        title="[CRITICAL] Suez Canal: Major blockage",
        summary="Risk Score: 0.85 | Zone: Suez Canal",
        geo_zone="suez_canal",
        pushed_at=None,
        created_at=datetime.now(timezone.utc),
    )


# ── Mock Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_db_conn() -> AsyncMock:
    """Mock async database connection."""
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetchone = AsyncMock()
    conn.fetchall = AsyncMock(return_value=[])
    return conn


@pytest.fixture
def mock_qdrant() -> AsyncMock:
    """Mock Qdrant async client."""
    client = AsyncMock()
    client.search = AsyncMock(return_value=[])
    client.upsert = AsyncMock()
    client.get_collection = AsyncMock()
    return client
