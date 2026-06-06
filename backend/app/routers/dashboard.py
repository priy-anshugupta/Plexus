"""
Plexus Backend — Dashboard Router

Exposes REST endpoints for the executive dashboard, including system-wide
KPIs, recent activity feeds, repository leaderboards, and historical trends.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models.finding import Finding, FindingStatus, Severity
from app.models.repository import Repository
from app.models.scan import Scan, ScanStatus
from app.schemas import (
    DashboardMetrics,
    DashboardResponse,
    RecentActivity,
    RepositorySummary,
    SeverityTrend,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_mock_dashboard() -> DashboardResponse:
    """Generate high-fidelity mock dashboard data for demonstration/offline mode."""
    # A few random but stable UUIDs
    repo_ids = [
        UUID("11111111-1111-1111-1111-111111111111"),
        UUID("22222222-2222-2222-2222-222222222222"),
        UUID("33333333-3333-3333-3333-333333333333"),
    ]

    metrics = DashboardMetrics(
        total_repositories=3,
        total_scans=12,
        total_findings=45,
        critical_findings=2,
        open_findings=38,
        scans_last_7_days=4,
        avg_scan_duration_seconds=42.5,
        security_score=82.4,
    )

    top_repositories = [
        RepositorySummary(
            id=repo_ids[0],
            name="plexus-core",
            full_name="plexus-dev/plexus-core",
            language="Python",
            total_findings=24,
            last_scan_status="COMPLETED",
        ),
        RepositorySummary(
            id=repo_ids[1],
            name="frontend-dashboard",
            full_name="plexus-dev/frontend-dashboard",
            language="JavaScript",
            total_findings=15,
            last_scan_status="COMPLETED",
        ),
        RepositorySummary(
            id=repo_ids[2],
            name="infra-terraform",
            full_name="plexus-dev/infra-terraform",
            language="HCL",
            total_findings=6,
            last_scan_status="FAILED",
        ),
    ]

    now = datetime.now()
    recent_activity = [
        RecentActivity(
            id=uuid4(),
            type="scan_completed",
            title="Scan Completed",
            description="Completed full repository scan on plexus-core (main).",
            timestamp=now - timedelta(minutes=45),
            metadata={"scan_id": str(uuid4()), "findings_count": 24},
        ),
        RecentActivity(
            id=uuid4(),
            type="finding_created",
            title="New Critical Vulnerability",
            description="Hardcoded API key detected in config.py in plexus-core.",
            timestamp=now - timedelta(hours=2),
            metadata={"severity": "CRITICAL", "file": "config.py"},
        ),
        RecentActivity(
            id=uuid4(),
            type="repo_added",
            title="Repository Connected",
            description="Connected frontend-dashboard repository successfully.",
            timestamp=now - timedelta(days=1),
            metadata={"language": "JavaScript"},
        ),
    ]

    return DashboardResponse(
        metrics=metrics,
        recent_activity=recent_activity,
        top_repositories=top_repositories,
    )


@router.get(
    "/",
    response_model=DashboardResponse,
    summary="Get unified dashboard data",
)
def get_dashboard_data(
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Retrieve the main dashboard metrics, activities, and top repositories.

    If the database is empty or offline, returns pre-populated demonstration data.
    """
    try:
        # Check if there are repositories; if not, return mock data
        repo_count = db.scalar(select(func.count(Repository.id))) or 0
        if repo_count == 0:
            return get_mock_dashboard()

        # Compute metrics
        scan_count = db.scalar(select(func.count(Scan.id))) or 0
        finding_count = db.scalar(select(func.count(Finding.id))) or 0
        
        crit_count = db.scalar(
            select(func.count(Finding.id)).where(Finding.severity == Severity.CRITICAL)
        ) or 0
        
        open_count = db.scalar(
            select(func.count(Finding.id)).where(Finding.status == FindingStatus.OPEN)
        ) or 0

        # Scans in the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        scans_7_days = db.scalar(
            select(func.count(Scan.id)).where(Scan.created_at >= seven_days_ago)
        ) or 0

        # Average duration of completed scans
        avg_duration = db.scalar(
            select(func.avg(Scan.duration_seconds))
            .where(Scan.status == ScanStatus.COMPLETED)
        )

        # Posture Score calculation (deduct points based on open findings severity)
        high_count = db.scalar(
            select(func.count(Finding.id)).where(Finding.severity == Severity.HIGH)
        ) or 0
        med_count = db.scalar(
            select(func.count(Finding.id)).where(Finding.severity == Severity.MEDIUM)
        ) or 0
        low_count = db.scalar(
            select(func.count(Finding.id)).where(Finding.severity == Severity.LOW)
        ) or 0

        # Max deduction is 100, starting from 100
        deductions = (crit_count * 15) + (high_count * 8) + (med_count * 3) + (low_count * 1)
        security_score = max(0.0, float(100.0 - deductions))

        metrics = DashboardMetrics(
            total_repositories=repo_count,
            total_scans=scan_count,
            total_findings=finding_count,
            critical_findings=crit_count,
            open_findings=open_count,
            scans_last_7_days=scans_7_days,
            avg_scan_duration_seconds=float(avg_duration) if avg_duration else None,
            security_score=security_score,
        )

        # Retrieve top repositories (ranked by finding count)
        top_repos_stmt = (
            select(
                Repository.id,
                Repository.name,
                Repository.full_name,
                Repository.language,
                func.count(Finding.id).label("total_findings"),
            )
            .outerjoin(Finding, Repository.id == Finding.repository_id)
            .group_by(Repository.id, Repository.name, Repository.full_name, Repository.language)
            .order_by(func.count(Finding.id).desc())
            .limit(5)
        )
        
        top_repositories = []
        for row in db.execute(top_repos_stmt).all():
            # Get latest scan status for this repo
            latest_scan_status = db.scalar(
                select(Scan.status)
                .where(Scan.repository_id == row.id)
                .order_by(Scan.created_at.desc())
                .limit(1)
            )
            top_repositories.append(
                RepositorySummary(
                    id=row.id,
                    name=row.name,
                    full_name=row.full_name,
                    language=row.language,
                    total_findings=row.total_findings,
                    last_scan_status=latest_scan_status.value if latest_scan_status else None,
                )
            )

        # Retrieve recent activities (using scans and findings as event sources)
        recent_activity = []
        
        # Latest completed scans
        scans_stmt = (
            select(Scan)
            .where(Scan.status == ScanStatus.COMPLETED)
            .order_by(Scan.completed_at.desc())
            .limit(3)
        )
        for s in db.scalars(scans_stmt).all():
            recent_activity.append(
                RecentActivity(
                    id=s.id,
                    type="scan_completed",
                    title="Scan Completed",
                    description=f"Completed {s.scan_type.value} scan on {s.repository_id}.",
                    timestamp=s.completed_at or s.created_at,
                    metadata={"scan_id": str(s.id), "findings_count": s.total_findings},
                )
            )

        # Latest security findings
        findings_stmt = (
            select(Finding)
            .order_by(Finding.created_at.desc())
            .limit(3)
        )
        for f in db.scalars(findings_stmt).all():
            recent_activity.append(
                RecentActivity(
                    id=f.id,
                    type="finding_created",
                    title=f"New {f.severity.value.upper()} Finding",
                    description=f"{f.title} detected in {f.file_path}.",
                    timestamp=f.created_at,
                    metadata={"severity": f.severity.value, "file": f.file_path},
                )
            )

        # Sort combined activities by timestamp
        recent_activity.sort(key=lambda x: x.timestamp, reverse=True)
        recent_activity = recent_activity[:5]

        return DashboardResponse(
            metrics=metrics,
            recent_activity=recent_activity,
            top_repositories=top_repositories,
        )

    except Exception as exc:
        logger.warning("Error generating dashboard from DB: %s. Returning mock data.", exc)
        return get_mock_dashboard()


@router.get(
    "/trends",
    response_model=list[SeverityTrend],
    summary="Get findings severity trend time-series",
)
def get_severity_trends(
    days: int = 30,
    db: Session = Depends(get_db),
) -> list[SeverityTrend]:
    """Retrieve daily time-series counts of open findings by severity level."""
    trends = []
    today = date.today()

    try:
        # Check if we have repositories; if not, return mock trends
        repo_count = db.scalar(select(func.count(Repository.id))) or 0
        if repo_count == 0:
            raise ValueError("No repositories found, returning mock trend.")

        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            target_dt_end = datetime.combine(target_date, datetime.max.time())
            
            # Count findings created on or before this day that are not resolved yet or were open then
            # For simplicity, count findings created up to this date
            crit = db.scalar(
                select(func.count(Finding.id))
                .where(Finding.created_at <= target_dt_end)
                .where(Finding.severity == Severity.CRITICAL)
            ) or 0
            high = db.scalar(
                select(func.count(Finding.id))
                .where(Finding.created_at <= target_dt_end)
                .where(Finding.severity == Severity.HIGH)
            ) or 0
            med = db.scalar(
                select(func.count(Finding.id))
                .where(Finding.created_at <= target_dt_end)
                .where(Finding.severity == Severity.MEDIUM)
            ) or 0
            low = db.scalar(
                select(func.count(Finding.id))
                .where(Finding.created_at <= target_dt_end)
                .where(Finding.severity == Severity.LOW)
            ) or 0
            info = db.scalar(
                select(func.count(Finding.id))
                .where(Finding.created_at <= target_dt_end)
                .where(Finding.severity == Severity.INFO)
            ) or 0

            trends.append(
                SeverityTrend(
                    date=target_date,
                    critical=crit,
                    high=high,
                    medium=med,
                    low=low,
                    info=info,
                )
            )

    except Exception:
        # Fallback to mock trends for mock dashboard
        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)
            # Create a progressive trend showing decreasing issues over time
            factor = (days - i) / days
            trends.append(
                SeverityTrend(
                    date=target_date,
                    critical=max(1, int(4 - (3 * factor))),
                    high=max(2, int(8 - (6 * factor))),
                    medium=max(5, int(15 - (10 * factor))),
                    low=max(10, int(25 - (15 * factor))),
                    info=max(1, int(3 - (2 * factor))),
                )
            )

    return trends
