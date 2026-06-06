"""
Plexus Backend — FastAPI Application Entry Point

Initializes the FastAPI application with CORS middleware, loads configuration,
and exposes the health check endpoint used by Docker and monitoring tools.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade DevEx & Security Posture Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Returns the current health status of the Plexus API."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
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
