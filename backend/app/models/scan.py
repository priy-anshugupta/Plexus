"""
Plexus Backend — Scan Model

Tracks every code-analysis run against a repository.  Each ``Scan`` records
its trigger, type, timing, status, and summary statistics.  Individual
issues found during the scan are stored as ``Finding`` rows.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ScanStatus(str, enum.Enum):
    """Lifecycle states of a scan."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, enum.Enum):
    """The kind of analysis performed."""

    FULL = "full"
    INCREMENTAL = "incremental"
    PR_REVIEW = "pr_review"


class Scan(UUIDMixin, TimestampMixin, Base):
    """A single code-analysis run against a repository."""

    __tablename__ = "scans"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID,
        sa.ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by: Mapped[uuid.UUID] = mapped_column(
        sa.UUID,
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    scan_type: Mapped[ScanType] = mapped_column(
        sa.Enum(ScanType, name="scan_type", native_enum=False),
        nullable=False,
    )
    status: Mapped[ScanStatus] = mapped_column(
        sa.Enum(ScanStatus, name="scan_status", native_enum=False),
        default=ScanStatus.PENDING,
        nullable=False,
    )

    branch: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    commit_sha: Mapped[Optional[str]] = mapped_column(sa.String(40), nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        sa.Float, nullable=True
    )

    total_findings: Mapped[int] = mapped_column(
        sa.Integer, default=0, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    # --- Relationships ---
    repository: Mapped["Repository"] = relationship(  # noqa: F821
        "Repository", back_populates="scans"
    )
    triggered_by_user: Mapped[Optional["User"]] = relationship("User")  # noqa: F821
    findings: Mapped[list["Finding"]] = relationship(  # noqa: F821
        "Finding", back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scan {self.id} status={self.status.value}>"
