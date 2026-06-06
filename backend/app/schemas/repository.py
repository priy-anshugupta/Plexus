"""
Plexus Backend — Repository API Schemas

Pydantic v2 models for creating, updating, listing, and summarising
source-code repositories tracked by the platform.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import PaginatedResponse


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class RepositoryCreate(BaseModel):
    """Payload for registering a new repository."""

    name: str = Field(..., min_length=1, max_length=255, description="Short repository name.")
    clone_url: HttpUrl = Field(..., description="HTTPS clone URL of the repository.")
    default_branch: str = Field(
        default="main",
        min_length=1,
        max_length=128,
        description="Default branch to scan.",
    )
    description: str | None = Field(default=None, max_length=1024, description="Optional description.")


class RepositoryUpdate(BaseModel):
    """Partial-update payload — every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255, description="Short repository name.")
    clone_url: HttpUrl | None = Field(default=None, description="HTTPS clone URL.")
    default_branch: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Default branch to scan.",
    )
    description: str | None = Field(default=None, max_length=1024, description="Optional description.")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class RepositoryResponse(BaseModel):
    """Full representation of a repository returned by detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    full_name: str = Field(..., description="Owner-qualified name, e.g. 'org/repo'.")
    clone_url: HttpUrl
    default_branch: str
    description: str | None = None
    language: str | None = Field(default=None, description="Primary programming language.")
    is_active: bool = Field(default=True, description="Whether the repo is actively monitored.")
    last_scanned_at: datetime | None = Field(
        default=None,
        description="Timestamp of the most recent completed scan.",
    )
    created_at: datetime
    updated_at: datetime


class RepositoryListResponse(PaginatedResponse[RepositoryResponse]):
    """Paginated list of repositories."""


class RepositorySummary(BaseModel):
    """Lightweight repository overview used on dashboards and leaderboards."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    full_name: str
    language: str | None = None
    total_findings: int = Field(default=0, ge=0, description="Aggregate finding count.")
    last_scan_status: str | None = Field(
        default=None,
        description="Status of the latest scan, e.g. 'COMPLETED', 'FAILED'.",
    )
