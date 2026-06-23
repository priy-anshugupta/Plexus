"""
Plexus Backend — Global Error Handling Middleware

Defines a hierarchy of application-specific exceptions and registers
FastAPI exception handlers that return a consistent JSON error envelope::

    {"error": "...", "detail": "...", "status_code": N}

All unhandled exceptions are caught, logged, and converted to a safe 500
response so that stack traces never leak to the client.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class PlexusException(Exception):
    """Base exception for all Plexus domain errors.

    Subclasses set ``status_code`` and ``detail`` so the global handler
    can construct an appropriate HTTP response automatically.

    Args:
        detail: Human-readable explanation of the error.
        status_code: HTTP status code to return (default 500).
    """

    def __init__(
        self,
        detail: str = "An unexpected error occurred.",
        status_code: int = 500,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundException(PlexusException):
    """Raised when a requested resource does not exist (HTTP 404)."""

    def __init__(self, detail: str = "Resource not found.") -> None:
        super().__init__(detail=detail, status_code=404)


class ConflictException(PlexusException):
    """Raised when a request conflicts with the current state (HTTP 409)."""

    def __init__(self, detail: str = "Conflict with existing resource.") -> None:
        super().__init__(detail=detail, status_code=409)


class DatabaseUnavailableException(PlexusException):
    """Raised when the database backend is unreachable (HTTP 503)."""

    def __init__(
        self,
        detail: str = "Database is temporarily unavailable. Please try again later.",
    ) -> None:
        super().__init__(detail=detail, status_code=503)


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------

def register_error_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application.

    Three handlers are registered:

    1. **PlexusException** — maps domain exceptions to their declared
       status code and detail message.
    2. **RequestValidationError** — returns a 422 with Pydantic
       validation details.
    3. **Exception** (catch-all) — logs the traceback and returns a
       generic 500 response so internals are never exposed to the client.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(PlexusException)
    async def plexus_exception_handler(
        request: Request,
        exc: PlexusException,
    ) -> JSONResponse:
        """Handle known Plexus domain exceptions."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": type(exc).__name__,
            "detail": exc.detail,
            "status_code": exc.status_code,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic / FastAPI request-validation errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "ValidationError",
            "detail": str(exc.errors()),
            "status_code": 422,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=422, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all for unhandled exceptions — log and return 500."""
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled exception on %s %s (req=%s)", request.method, request.url, request_id)
        content = {
            "error": "InternalServerError",
            "detail": "An unexpected error occurred.",
            "status_code": 500,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=500, content=content)
