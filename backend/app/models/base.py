"""
Plexus Backend — SQLAlchemy Declarative Base & Shared Mixins

Provides the ``Base`` declarative class for all ORM models, along with
reusable mixins for UUID primary keys and automatic timestamp columns.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for every SQLAlchemy ORM model in Plexus."""

    pass


class UUIDMixin:
    """Mixin that adds a UUID ``id`` primary key column.

    The default is generated in Python via :func:`uuid.uuid4`.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID,
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` audit columns.

    Both columns are timezone-aware.  ``updated_at`` is refreshed
    automatically on every UPDATE statement.
    """

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
