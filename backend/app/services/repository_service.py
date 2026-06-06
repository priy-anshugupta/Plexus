"""
Plexus Backend — Repository Service

Encapsulates all CRUD operations for the ``Repository`` model.  Accepts a
synchronous SQLAlchemy ``Session`` and returns ORM instances directly so
callers can rely on Pydantic's ``from_attributes`` for serialisation.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Repository
from app.schemas import RepositoryCreate, RepositoryUpdate

logger = logging.getLogger(__name__)


class RepositoryService:
    """Repository business-logic layer.

    Usage::

        service = RepositoryService(db_session)
        repo = service.create(RepositoryCreate(name="my-repo", ...))
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, data: RepositoryCreate) -> Repository:
        """Persist a new repository record.

        The ``full_name`` is derived from the repo ``name`` when not
        otherwise provided (owner context will be added in a future auth
        iteration).

        Args:
            data: Validated creation payload.

        Returns:
            The newly created ``Repository`` ORM instance.
        """
        repo = Repository(
            name=data.name,
            full_name=data.name,  # placeholder until org/owner context exists
            clone_url=str(data.clone_url),
            default_branch=data.default_branch,
            description=data.description,
            # owner_id will be set from the authenticated user in a future iteration
        )
        self._session.add(repo)
        self._session.flush()
        self._session.refresh(repo)
        return repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, repo_id: UUID) -> Repository | None:
        """Fetch a single repository by its primary key.

        Args:
            repo_id: UUID of the repository.

        Returns:
            The ``Repository`` if found, otherwise ``None``.
        """
        return self._session.get(Repository, repo_id)

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Repository], int]:
        """Return a paginated list of repositories and the total count.

        Args:
            page: 1-based page number.
            page_size: Maximum items per page.

        Returns:
            A tuple of ``(repositories, total_count)``.
        """
        total: int = self._session.scalar(
            select(func.count()).select_from(Repository)
        ) or 0

        stmt = (
            select(Repository)
            .order_by(Repository.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        repos = list(self._session.scalars(stmt).all())
        return repos, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, repo_id: UUID, data: RepositoryUpdate) -> Repository | None:
        """Apply a partial update to an existing repository.

        Only fields explicitly set in ``data`` (non-``None``) are written.

        Args:
            repo_id: UUID of the repository to update.
            data: Validated partial-update payload.

        Returns:
            The updated ``Repository``, or ``None`` if not found.
        """
        repo = self.get_by_id(repo_id)
        if repo is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "clone_url" and value is not None:
                value = str(value)
            setattr(repo, field, value)

        self._session.flush()
        self._session.refresh(repo)
        return repo

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, repo_id: UUID) -> bool:
        """Remove a repository by primary key.

        Args:
            repo_id: UUID of the repository to delete.

        Returns:
            ``True`` if the record was found and deleted, ``False`` otherwise.
        """
        repo = self.get_by_id(repo_id)
        if repo is None:
            return False

        self._session.delete(repo)
        self._session.flush()
        return True
