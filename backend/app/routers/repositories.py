"""
Plexus Backend — Repository Router

Exposes REST endpoints for managing repository configurations, mapping
incoming requests to the repository service.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.database import get_db
from app.middleware.error_handler import NotFoundException
from app.schemas import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
    RepositoryUpdate,
    StatusResponse,
)
from app.services.repository_service import RepositoryService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post(
    "/",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new repository",
)
def create_repository(
    data: RepositoryCreate,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    """Create a new repository configuration for security/code quality scanning."""
    service = RepositoryService(db)
    return service.create(data)


@router.get(
    "/",
    response_model=RepositoryListResponse,
    summary="List repositories with pagination",
)
def list_repositories(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> RepositoryListResponse:
    """Retrieve a paginated list of registered repositories."""
    service = RepositoryService(db)
    repos, total = service.list_all(page=page, page_size=page_size)
    return RepositoryListResponse(
        items=repos,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{repo_id}",
    response_model=RepositoryResponse,
    summary="Get repository details",
)
def get_repository(
    repo_id: UUID,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    """Retrieve details of a single repository by its UUID."""
    service = RepositoryService(db)
    repo = service.get_by_id(repo_id)
    if repo is None:
        raise NotFoundException(f"Repository with ID {repo_id} not found.")
    return repo


@router.patch(
    "/{repo_id}",
    response_model=RepositoryResponse,
    summary="Update a repository configuration",
)
def update_repository(
    repo_id: UUID,
    data: RepositoryUpdate,
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    """Apply partial updates to a repository configuration."""
    service = RepositoryService(db)
    repo = service.update(repo_id, data)
    if repo is None:
        raise NotFoundException(f"Repository with ID {repo_id} not found.")
    return repo


@router.delete(
    "/{repo_id}",
    response_model=StatusResponse,
    summary="Delete a repository",
)
def delete_repository(
    repo_id: UUID,
    db: Session = Depends(get_db),
) -> StatusResponse:
    """Remove a repository configuration from the platform."""
    service = RepositoryService(db)
    deleted = service.delete(repo_id)
    if not deleted:
        raise NotFoundException(f"Repository with ID {repo_id} not found.")
    return StatusResponse(
        status="success",
        message=f"Repository {repo_id} deleted successfully.",
    )
