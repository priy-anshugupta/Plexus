"""
Plexus Backend — Finding Router

Exposes REST endpoints for browsing security and code quality findings,
updating triage status, and gathering aggregate statistics.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.middleware.error_handler import NotFoundException
from app.models.finding import Finding, FindingCategory, FindingStatus, Severity
from app.schemas import FindingListResponse, FindingResponse, FindingStats, FindingUpdate
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["Findings"])

# Map schema status inputs to model enums
STATUS_MAP = {
    "open": FindingStatus.OPEN,
    "acknowledged": FindingStatus.ACKNOWLEDGED,
    "confirmed": FindingStatus.ACKNOWLEDGED,
    "false_positive": FindingStatus.FALSE_POSITIVE,
    "fixed": FindingStatus.FIXED,
    "resolved": FindingStatus.FIXED,
}


@router.get(
    "/",
    response_model=FindingListResponse,
    summary="List findings with filtering and pagination",
)
def list_findings(
    page: int = 1,
    page_size: int = 20,
    severity: str | None = None,
    category: str | None = None,
    status: str | None = None,
    repository_id: UUID | None = None,
    db: Session = Depends(get_db),
) -> FindingListResponse:
    """Retrieve a paginated list of security/code quality findings with optional filters."""
    stmt = select(Finding)

    if severity:
        try:
            sev_val = Severity(severity.lower())
            stmt = stmt.where(Finding.severity == sev_val)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity filter. Choose from: {[s.value for s in Severity]}",
            )

    if category:
        try:
            cat_val = FindingCategory(category.lower())
            stmt = stmt.where(Finding.category == cat_val)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category filter. Choose from: {[c.value for c in FindingCategory]}",
            )

    if status:
        stat_val = STATUS_MAP.get(status.lower())
        if not stat_val:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status filter. Choose from: {list(STATUS_MAP.keys())}",
            )
        stmt = stmt.where(Finding.status == stat_val)

    if repository_id:
        stmt = stmt.where(Finding.repository_id == repository_id)

    # Count total matching records
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # Paginate and fetch
    stmt = (
        stmt.order_by(Finding.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    findings = list(db.scalars(stmt).all())

    return FindingListResponse(
        items=findings,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats",
    response_model=FindingStats,
    summary="Get finding statistics",
)
def get_finding_stats(
    repository_id: UUID | None = None,
    db: Session = Depends(get_db),
) -> FindingStats:
    """Retrieve aggregated finding statistics (total, by severity, category, and status)."""
    # 1. Severity stats
    sev_stmt = select(Finding.severity, func.count(Finding.id))
    if repository_id:
        sev_stmt = sev_stmt.where(Finding.repository_id == repository_id)
    sev_stmt = sev_stmt.group_by(Finding.severity)
    
    # 2. Category stats
    cat_stmt = select(Finding.category, func.count(Finding.id))
    if repository_id:
        cat_stmt = cat_stmt.where(Finding.repository_id == repository_id)
    cat_stmt = cat_stmt.group_by(Finding.category)

    # 3. Status stats
    stat_stmt = select(Finding.status, func.count(Finding.id))
    if repository_id:
        stat_stmt = stat_stmt.where(Finding.repository_id == repository_id)
    stat_stmt = stat_stmt.group_by(Finding.status)

    try:
        by_severity = {sev.value: count for sev, count in db.execute(sev_stmt).all()}
        by_category = {cat.value: count for cat, count in db.execute(cat_stmt).all()}
        by_status = {stat.value: count for stat, count in db.execute(stat_stmt).all()}
        total = sum(by_severity.values())
    except Exception as exc:
        logger.warning("Error fetching statistics from DB: %s", exc)
        by_severity, by_category, by_status, total = {}, {}, {}, 0

    return FindingStats(
        total=total,
        by_severity=by_severity,
        by_category=by_category,
        by_status=by_status,
    )


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Get finding details",
)
def get_finding(
    finding_id: UUID,
    db: Session = Depends(get_db),
) -> FindingResponse:
    """Retrieve details of a single finding by its UUID."""
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise NotFoundException(f"Finding with ID {finding_id} not found.")
    return finding


@router.patch(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Update finding triage status",
)
def update_finding(
    finding_id: UUID,
    data: FindingUpdate,
    db: Session = Depends(get_db),
) -> FindingResponse:
    """Update the triage status of a finding (e.g., mark as FALSE_POSITIVE or FIXED)."""
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise NotFoundException(f"Finding with ID {finding_id} not found.")

    new_status = STATUS_MAP.get(data.status.lower())
    if not new_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status value. Choose from: {list(STATUS_MAP.keys())}",
        )

    finding.status = new_status
    db.flush()
    db.refresh(finding)
    return finding
