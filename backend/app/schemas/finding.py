"""
Plexus Backend — Finding API Schemas

Pydantic v2 models for security / code-quality findings surfaced by the
scanning pipeline. Includes detail views, status updates, and aggregate
statistics.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class FindingResponse(BaseModel):
    """Full representation of a single finding."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scan_id: UUID
    repository_id: UUID
    file_path: str = Field(..., description="Relative file path inside the repository.")
    line_start: int = Field(..., ge=1, description="Starting line number.")
    line_end: int | None = Field(default=None, ge=1, description="Ending line number (inclusive).")
    severity: str = Field(
        ...,
        description="Severity level — 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'.",
    )
    category: str = Field(
        ...,
        description="Finding category, e.g. 'SQL_INJECTION', 'XSS', 'DEPENDENCY'.",
    )
    status: str = Field(
        ...,
        description="Triage status — 'OPEN', 'CONFIRMED', 'FALSE_POSITIVE', 'RESOLVED'.",
    )
    title: str = Field(..., description="Short summary of the finding.")
    description: str = Field(..., description="Detailed explanation.")
    suggestion: str | None = Field(
        default=None,
        description="Recommended fix or remediation guidance.",
    )
    code_snippet: str | None = Field(
        default=None,
        description="Relevant source-code excerpt surrounding the issue.",
    )
    rule_id: str | None = Field(
        default=None,
        description="Identifier of the rule that triggered this finding.",
    )
    confidence_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in the finding (0.0–1.0).",
    )
    is_ai_generated: bool = Field(
        default=False,
        description="Whether the finding was produced by an AI model.",
    )
    created_at: datetime


class FindingListResponse(PaginatedResponse[FindingResponse]):
    """Paginated list of findings."""


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class FindingUpdate(BaseModel):
    """Payload for updating a finding's triage status.

    Only the ``status`` field is user-writable; all other finding data is
    immutable once created by the scanner.
    """

    status: str = Field(
        ...,
        description="New triage status — 'OPEN', 'CONFIRMED', 'FALSE_POSITIVE', 'RESOLVED'.",
    )


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class FindingStats(BaseModel):
    """Aggregate finding statistics, typically scoped to a repository or scan."""

    total: int = Field(..., ge=0, description="Total number of findings.")
    by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="Finding count keyed by severity level.",
    )
    by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Finding count keyed by category.",
    )
    by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Finding count keyed by triage status.",
    )
