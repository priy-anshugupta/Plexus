"""
Plexus Backend — Dashboard API Schemas

Pydantic v2 models for the executive dashboard: aggregate metrics,
recent activity feed, top-repository rankings, and severity trend
time-series.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.repository import RepositorySummary


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class DashboardMetrics(BaseModel):
    """High-level KPIs displayed on the main dashboard."""

    total_repositories: int = Field(..., ge=0)
    total_scans: int = Field(..., ge=0)
    total_findings: int = Field(..., ge=0)
    critical_findings: int = Field(..., ge=0, description="Findings with CRITICAL severity.")
    open_findings: int = Field(..., ge=0, description="Findings still in OPEN status.")
    scans_last_7_days: int = Field(..., ge=0, description="Scans executed in the last 7 calendar days.")
    avg_scan_duration_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Average scan wall-clock duration across all completed scans.",
    )
    security_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Composite security posture score (0–100, higher is better).",
    )


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------

class RecentActivity(BaseModel):
    """Single entry in the dashboard activity timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: Literal["scan_completed", "finding_created", "repo_added"] = Field(
        ...,
        description="Activity event type.",
    )
    title: str = Field(..., description="Short headline for the activity card.")
    description: str = Field(..., description="Human-readable detail.")
    timestamp: datetime = Field(..., description="When the event occurred.")
    metadata: dict | None = Field(
        default=None,
        description="Optional structured context (e.g. scan ID, severity counts).",
    )


# ---------------------------------------------------------------------------
# Severity Trend
# ---------------------------------------------------------------------------

class SeverityTrend(BaseModel):
    """Daily severity distribution used for trend charts."""

    date: date
    critical: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    low: int = Field(default=0, ge=0)
    info: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Composite Dashboard
# ---------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    """Complete payload returned by the ``GET /dashboard`` endpoint."""

    metrics: DashboardMetrics
    recent_activity: list[RecentActivity] = Field(
        default_factory=list,
        description="Most recent platform events.",
    )
    top_repositories: list[RepositorySummary] = Field(
        default_factory=list,
        description="Repositories ranked by finding count.",
    )
