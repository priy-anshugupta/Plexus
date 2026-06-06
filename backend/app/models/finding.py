"""
Plexus Backend — Finding Model

Represents a single issue discovered during a code scan.  Findings are
categorised by severity, domain, and current triage status.  They may
include AI-generated suggestions and confidence scores.
"""

from __future__ import annotations

import enum
import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Severity(str, enum.Enum):
    """How critical the finding is."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, enum.Enum):
    """Domain the finding belongs to."""

    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


class FindingStatus(str, enum.Enum):
    """Triage state of a finding."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    FALSE_POSITIVE = "false_positive"
    FIXED = "fixed"


class Finding(UUIDMixin, TimestampMixin, Base):
    """An individual issue detected during a scan."""

    __tablename__ = "findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID,
        sa.ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID,
        sa.ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    line_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    line_end: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)

    severity: Mapped[Severity] = mapped_column(
        sa.Enum(Severity, name="finding_severity", native_enum=False),
        nullable=False,
    )
    category: Mapped[FindingCategory] = mapped_column(
        sa.Enum(FindingCategory, name="finding_category", native_enum=False),
        nullable=False,
    )
    status: Mapped[FindingStatus] = mapped_column(
        sa.Enum(FindingStatus, name="finding_status", native_enum=False),
        default=FindingStatus.OPEN,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    suggestion: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    rule_id: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    confidence_score: Mapped[float] = mapped_column(sa.Float, nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, nullable=False
    )

    # --- Relationships ---
    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")  # noqa: F821
    repository: Mapped["Repository"] = relationship("Repository")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Finding {self.title!r} severity={self.severity.value}>"
