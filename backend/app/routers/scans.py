"""
Plexus Backend — Scan Router

Exposes REST endpoints for triggering scans, checking scan status,
listing scan history, and cancelling active scans.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.database import get_db
from app.middleware.error_handler import NotFoundException
from app.schemas import ScanListResponse, ScanResponse, ScanTrigger
from app.services.repository_service import RepositoryService
from app.services.scan_service import ScanService
from app.services.scanner_service import ScannerService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scans", tags=["Scans"])

# Hardcoded placeholder user ID since authentication/user accounts are not yet wired up.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")

scanner_service = ScannerService()


@router.post(
    "/",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a new scan",
)
def trigger_scan(
    data: ScanTrigger,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ScanResponse:
    """Initiate a security and code quality scan on a registered repository."""
    # First verify that the repository exists
    repo_service = RepositoryService(db)
    repo = repo_service.get_by_id(data.repository_id)
    if repo is None:
        raise NotFoundException(f"Repository with ID {data.repository_id} not found.")

    scan_service = ScanService(db)
    scan = scan_service.trigger_scan(data, user_id=SYSTEM_USER_ID)
    
    # Run the clone, AST analysis and findings generation in the background
    background_tasks.add_task(scanner_service.run_scan, scan.id)
    
    return scan


@router.get(
    "/",
    response_model=ScanListResponse,
    summary="List all scans across repositories",
)
def list_scans(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> ScanListResponse:
    """Retrieve a paginated list of recent scan executions across all repositories."""
    scan_service = ScanService(db)
    scans, total = scan_service.list_recent(page=page, page_size=page_size)
    return ScanListResponse(
        items=scans,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="Get scan status and details",
)
def get_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
) -> ScanResponse:
    """Retrieve the status and results summary of a single scan."""
    scan_service = ScanService(db)
    scan = scan_service.get_by_id(scan_id)
    if scan is None:
        raise NotFoundException(f"Scan with ID {scan_id} not found.")
    return scan


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanResponse,
    summary="Cancel an active scan",
)
def cancel_scan(
    scan_id: UUID,
    db: Session = Depends(get_db),
) -> ScanResponse:
    """Request cancellation of an active or pending scan.

    Returns the updated scan model or raises 404 if the scan does not exist,
    or returns the unmodified scan state if it is already finished/cancelled.
    """
    scan_service = ScanService(db)
    # Check if the scan exists first to return proper 404 if missing
    scan = scan_service.get_by_id(scan_id)
    if scan is None:
        raise NotFoundException(f"Scan with ID {scan_id} not found.")

    cancelled_scan = scan_service.cancel_scan(scan_id)
    if cancelled_scan is None:
        # If cancel_scan returned None, it means the scan is already in a terminal state
        # Return the unmodified scan model as it is
        return scan
    return cancelled_scan


@router.get(
    "/repository/{repo_id}",
    response_model=ScanListResponse,
    summary="List scans for a repository",
)
def list_repository_scans(
    repo_id: UUID,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> ScanListResponse:
    """Retrieve a paginated list of scans executed for a specific repository."""
    # Verify repository exists
    repo_service = RepositoryService(db)
    repo = repo_service.get_by_id(repo_id)
    if repo is None:
        raise NotFoundException(f"Repository with ID {repo_id} not found.")

    scan_service = ScanService(db)
    scans, total = scan_service.list_by_repository(repo_id, page=page, page_size=page_size)
    return ScanListResponse(
        items=scans,
        total=total,
        page=page,
        page_size=page_size,
    )
