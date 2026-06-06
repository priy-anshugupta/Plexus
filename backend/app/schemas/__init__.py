"""
Plexus Backend — Schema Package

Re-exports key Pydantic v2 models for convenient access::

    from app.schemas import RepositoryCreate, ScanResponse, FindingStats
"""

# -- Common ----------------------------------------------------------------
from app.schemas.common import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    StatusResponse,
)

# -- Repository ------------------------------------------------------------
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
    RepositorySummary,
    RepositoryUpdate,
)

# -- Scan ------------------------------------------------------------------
from app.schemas.scan import (
    ScanListResponse,
    ScanProgress,
    ScanResponse,
    ScanTrigger,
)

# -- Finding ---------------------------------------------------------------
from app.schemas.finding import (
    FindingListResponse,
    FindingResponse,
    FindingStats,
    FindingUpdate,
)

# -- Dashboard -------------------------------------------------------------
from app.schemas.dashboard import (
    DashboardMetrics,
    DashboardResponse,
    RecentActivity,
    SeverityTrend,
)

__all__ = [
    # Common
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "PaginationParams",
    "StatusResponse",
    # Repository
    "RepositoryCreate",
    "RepositoryListResponse",
    "RepositoryResponse",
    "RepositorySummary",
    "RepositoryUpdate",
    # Scan
    "ScanListResponse",
    "ScanProgress",
    "ScanResponse",
    "ScanTrigger",
    # Finding
    "FindingListResponse",
    "FindingResponse",
    "FindingStats",
    "FindingUpdate",
    # Dashboard
    "DashboardMetrics",
    "DashboardResponse",
    "RecentActivity",
    "SeverityTrend",
]
