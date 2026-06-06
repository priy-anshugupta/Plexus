"""
Plexus Backend — Repository Model

Represents a Git repository being tracked and analysed by the platform.
Each repository belongs to a single owner (``User``) and may have many
associated ``Scan`` records.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Repository(UUIDMixin, TimestampMixin, Base):
    """A Git repository registered with Plexus for analysis."""

    __tablename__ = "repositories"

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(
        sa.String(512), unique=True, nullable=False
    )
    clone_url: Mapped[str] = mapped_column(sa.String(2048), nullable=False)
    default_branch: Mapped[str] = mapped_column(
        sa.String(255), default="main", nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(sa.String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # --- Relationships ---
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="repositories"
    )
    scans: Mapped[list["Scan"]] = relationship(  # noqa: F821
        "Scan", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository {self.full_name!r}>"
