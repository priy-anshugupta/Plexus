"""
Plexus Backend — FastAPI Application Entry Point

Initializes the FastAPI application with CORS middleware, registers routers
under /api/v1, attaches error handling middleware, manages the database lifespan,
and exposes health check endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db_manager
from app.middleware.error_handler import register_error_handlers
from app.routers import (
    dashboard_router,
    findings_router,
    repositories_router,
    scans_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown lifecycle of database connections."""
    # Connect to PostgreSQL, Neo4j, Qdrant, and Redis (offline-tolerant)
    await db_manager.startup()
    yield
    # Disconnect and dispose resources cleanly
    await db_manager.shutdown()


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade DevEx & Security Posture Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware — allows the Next.js frontend to communicate with the API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global Error Handlers
# ---------------------------------------------------------------------------
register_error_handlers(app)

# ---------------------------------------------------------------------------
# API Routers
# ---------------------------------------------------------------------------
app.include_router(repositories_router, prefix="/api/v1")
app.include_router(scans_router, prefix="/api/v1")
app.include_router(findings_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health Check (System level)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Returns the current health status of the Plexus API."""
    # Assess database connection health
    postgres_health = "connected" if db_manager.engine is not None else "offline"
    neo4j_health = "connected" if db_manager.neo4j_driver is not None else "offline"
    qdrant_health = "connected" if db_manager.qdrant_client is not None else "offline"
    redis_health = "connected" if db_manager.redis_client is not None else "offline"

    db_status = {
        "postgres": postgres_health,
        "neo4j": neo4j_health,
        "qdrant": qdrant_health,
        "redis": redis_health,
    }

    # If Postgres is down, system is degraded. If all are down, it's unhealthy
    connected_count = sum(1 for status in db_status.values() if status == "connected")
    if connected_count == 4:
        status_label = "healthy"
    elif postgres_health == "connected":
        status_label = "degraded"
    else:
        status_label = "unhealthy"

    return {
        "status": status_label,
        "service": settings.app_name,
        "environment": settings.app_env,
        "databases": db_status,
    }


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
