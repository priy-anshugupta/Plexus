"""
Plexus Backend — User & API Key Models

Defines the ``User`` table for platform identity and the ``APIKey`` table
for programmatic access tokens.  Relationships are configured so that
``user.api_keys`` returns associated keys.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """Permitted roles within the platform."""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(UUIDMixin, TimestampMixin, Base):
    """A registered Plexus platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        sa.String(320), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(sa.String(2048), nullable=True)
    github_username: Mapped[Optional[str]] = mapped_column(
        sa.String(255), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.MEMBER,
        nullable=False,
    )

    # --- Relationships ---
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    repositories: Mapped[list["Repository"]] = relationship(  # noqa: F821
        "Repository", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email!r}>"


class APIKey(UUIDMixin, TimestampMixin, Base):
    """A hashed API key granting programmatic access to Plexus."""

    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey {self.name!r} user={self.user_id}>"
