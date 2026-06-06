"""
Plexus Backend — Scan Service

Encapsulates CRUD and lifecycle operations for the ``Scan`` model.
Handles scan creation with initial PENDING status, listing with
pagination, and cancellation logic.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Scan, ScanStatus, ScanType
from app.schemas import ScanTrigger

logger = logging.getLogger(__name__)


class ScanService:
    """Scan business-logic layer.

    Usage::

        service = ScanService(db_session)
        scan = service.trigger_scan(ScanTrigger(...), user_id=...)
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Trigger (Create)
    # ------------------------------------------------------------------

    def trigger_scan(self, data: ScanTrigger, user_id: UUID) -> Scan:
        """Create a new scan record with ``PENDING`` status.

        Args:
            data: Validated scan trigger payload.
            user_id: UUID of the user who triggered the scan.

        Returns:
            The newly created ``Scan`` ORM instance.
        """
        # Map the schema scan_type string to the ScanType enum
        scan_type_map = {
            "FULL": ScanType.FULL,
            "INCREMENTAL": ScanType.INCREMENTAL,
            "PR": ScanType.PR_REVIEW,
        }
        scan_type = scan_type_map.get(data.scan_type.upper(), ScanType.FULL)

        scan = Scan(
            repository_id=data.repository_id,
            triggered_by=user_id,
            scan_type=scan_type,
            status=ScanStatus.PENDING,
            branch=data.branch,
            commit_sha=data.commit_sha,
        )
        self._session.add(scan)
        self._session.flush()
        self._session.refresh(scan)
        return scan

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, scan_id: UUID) -> Scan | None:
        """Fetch a single scan by its primary key.

        Args:
            scan_id: UUID of the scan.

        Returns:
            The ``Scan`` if found, otherwise ``None``.
        """
        return self._session.get(Scan, scan_id)

    def list_by_repository(
        self,
        repo_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Scan], int]:
        """Return a paginated list of scans for a specific repository.

        Args:
            repo_id: UUID of the repository.
            page: 1-based page number.
            page_size: Maximum items per page.

        Returns:
            A tuple of ``(scans, total_count)``.
        """
        base_filter = select(Scan).where(Scan.repository_id == repo_id)

        total: int = self._session.scalar(
            select(func.count()).select_from(base_filter.subquery())
        ) or 0

        stmt = (
            base_filter
            .order_by(Scan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        scans = list(self._session.scalars(stmt).all())
        return scans, total

    def list_recent(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Scan], int]:
        """Return a paginated list of the most recent scans across all repos.

        Args:
            page: 1-based page number.
            page_size: Maximum items per page.

        Returns:
            A tuple of ``(scans, total_count)``.
        """
        total: int = self._session.scalar(
            select(func.count()).select_from(Scan)
        ) or 0

        stmt = (
            select(Scan)
            .order_by(Scan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        scans = list(self._session.scalars(stmt).all())
        return scans, total

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def cancel_scan(self, scan_id: UUID) -> Scan | None:
        """Cancel a scan if it is still ``PENDING`` or ``RUNNING``.

        Scans in terminal states (``COMPLETED``, ``FAILED``, ``CANCELLED``)
        are **not** modified — the method returns ``None`` in those cases.

        Args:
            scan_id: UUID of the scan to cancel.

        Returns:
            The updated ``Scan`` with ``CANCELLED`` status, or ``None`` if
            the scan was not found or already in a terminal state.
        """
        scan = self.get_by_id(scan_id)
        if scan is None:
            return None

        if scan.status not in (ScanStatus.PENDING, ScanStatus.RUNNING):
            return None

        scan.status = ScanStatus.CANCELLED
        self._session.flush()
        self._session.refresh(scan)
        return scan
