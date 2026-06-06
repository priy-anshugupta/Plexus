"""
Plexus Backend — Router Package

Aggregates all API routers for clean import in ``main.py``.
"""

from __future__ import annotations

from app.routers.dashboard import router as dashboard_router
from app.routers.findings import router as findings_router
from app.routers.repositories import router as repositories_router
from app.routers.scans import router as scans_router
from app.routers.webhooks import router as webhooks_router

__all__ = [
    "dashboard_router",
    "findings_router",
    "repositories_router",
    "scans_router",
    "webhooks_router",
]
