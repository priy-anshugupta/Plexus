"""
Plexus Backend — Scan API Schemas

Pydantic v2 models for triggering scans, viewing scan results, and
tracking real-time scan progress via WebSocket or polling.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------

class ScanTrigger(BaseModel):
    """Payload for initiating a new scan on a repository."""

    repository_id: UUID = Field(..., description="Repository to scan.")
    scan_type: str = Field(
        default="FULL",
        description="Scan scope — 'FULL', 'INCREMENTAL', or 'PR'.",
    )
    branch: str | None = Field(
        default=None,
        description="Branch to scan. Defaults to the repository's default branch.",
    )
    commit_sha: str | None = Field(
        default=None,
        min_length=7,
        max_length=40,
        description="Specific commit SHA to scan (short or full).",
    )


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class ScanResponse(BaseModel):
    """Full representation of a completed or in-progress scan."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    scan_type: str
    status: str = Field(..., description="Current status — 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED'.")
    branch: str | None = None
    commit_sha: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = Field(
        default=None,
        ge=0,
        description="Wall-clock duration of the scan in seconds.",
    )
    total_findings: int = Field(default=0, ge=0, description="Number of findings produced.")
    error_message: str | None = Field(
        default=None,
        description="Error details when status is 'FAILED'.",
    )
    created_at: datetime


class ScanListResponse(PaginatedResponse[ScanResponse]):
    """Paginated list of scans."""


# ---------------------------------------------------------------------------
# Progress (WebSocket / polling)
# ---------------------------------------------------------------------------

class ScanProgress(BaseModel):
    """Real-time progress update for an active scan."""

    scan_id: UUID
    status: str = Field(..., description="Current scan status.")
    progress_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Completion percentage (0–100).",
    )
    current_step: str = Field(..., description="Human-readable step label, e.g. 'Analyzing dependencies'.")
    files_scanned: int = Field(default=0, ge=0, description="Files processed so far.")
    files_total: int = Field(default=0, ge=0, description="Total files to process.")
