"""
Plexus Backend — Common API Schemas

Shared Pydantic v2 models used across all API modules. Includes generic
pagination, error envelopes, health-check responses, and reusable status
messages.
"""

from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class StatusResponse(BaseModel):
    """Generic status message returned by mutation endpoints."""

    status: str = Field(..., description="Outcome indicator, e.g. 'success' or 'error'.")
    message: str = Field(..., description="Human-readable explanation of the result.")


class PaginationParams(BaseModel):
    """Query parameters accepted by every paginated list endpoint."""

    page: int = Field(default=1, ge=1, description="1-based page number.")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (1–100).",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Envelope for paginated list results.

    The ``total_pages`` value is derived automatically when the model is
    constructed, but callers may also supply it explicitly.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T] = Field(default_factory=list, description="Page of result items.")
    total: int = Field(..., ge=0, description="Total number of matching items across all pages.")
    page: int = Field(..., ge=1, description="Current page number.")
    page_size: int = Field(..., ge=1, description="Items per page.")
    total_pages: int = Field(default=0, ge=0, description="Total number of pages.")

    def model_post_init(self, __context: object) -> None:
        """Calculate ``total_pages`` when not supplied by the caller."""
        if self.total_pages == 0 and self.total > 0 and self.page_size > 0:
            object.__setattr__(
                self,
                "total_pages",
                math.ceil(self.total / self.page_size),
            )


class ErrorResponse(BaseModel):
    """Standard error envelope returned by exception handlers."""

    error: str = Field(..., description="Machine-readable error code or short label.")
    detail: str | None = Field(default=None, description="Optional human-readable explanation.")
    status_code: int = Field(..., description="HTTP status code mirrored in the body for convenience.")


class HealthResponse(BaseModel):
    """Response from the ``/health`` system endpoint."""

    status: str = Field(..., description="Overall health status ('healthy', 'degraded', 'unhealthy').")
    service: str = Field(..., description="Service name, e.g. 'Plexus'.")
    environment: str = Field(..., description="Running environment ('development', 'staging', 'production').")
    databases: dict[str, str] = Field(
        default_factory=dict,
        description="Per-database health, e.g. {'postgres': 'connected', 'neo4j': 'unreachable'}.",
    )
