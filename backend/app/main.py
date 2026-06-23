"""
Plexus Backend — FastAPI Application Entry Point

Initializes the FastAPI application with CORS middleware, registers routers
under /api/v1, attaches error handling middleware, manages the database lifespan,
and exposes health check endpoints.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import db_manager
from app.middleware.error_handler import register_error_handlers
from app.routers import (
    dashboard_router,
    findings_router,
    graph_router,
    repositories_router,
    scans_router,
    webhooks_router,
)


def configure_logging() -> None:
    """Configure structured JSON-like logging for production observability."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    # Quiet noisy third-party libraries
    for lib in ("urllib3", "httpx", "neo4j", "qdrant_client", "sqlalchemy.engine"):
        logging.getLogger(lib).setLevel(logging.WARNING)


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown lifecycle of database connections."""
    logger = logging.getLogger(__name__)
    logger.info("Starting up %s v%s", settings.app_name, "0.1.0")
    # Connect to PostgreSQL, Neo4j, Qdrant, and Redis (offline-tolerant)
    await db_manager.startup()
    yield
    # Disconnect and dispose resources cleanly
    await db_manager.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade DevEx & Security Posture Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request ID & Logging Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_logging(request: Request, call_next):
    """Attach a unique request ID and log request/response metrics."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.perf_counter()
    logger = logging.getLogger("plexus.access")
    logger.info(
        "[%s] %s %s started",
        request_id,
        request.method,
        request.url.path,
    )
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "[%s] %s %s -> %d in %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "[%s] %s %s failed in %.2fms: %s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )


# ---------------------------------------------------------------------------
# CORS Middleware — allows the Next.js frontend to communicate with the API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
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
app.include_router(graph_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")


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
