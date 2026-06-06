"""
Plexus Backend — Database Connection Manager

Manages connections to all four database backends used by Plexus:
PostgreSQL (relational), Neo4j (graph), Qdrant (vector), and Redis (cache).
Each connection is wrapped in try/except so the application can start even
when one or more databases are offline.  FastAPI dependency functions are
provided for convenient injection into route handlers.
"""

from __future__ import annotations

import logging
from typing import Generator

import redis
import sqlalchemy as sa
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralised manager for every database connection used by Plexus.

    Usage::

        db_manager = DatabaseManager()
        await db_manager.startup()   # call during FastAPI lifespan startup
        ...
        await db_manager.shutdown()  # call during FastAPI lifespan shutdown
    """

    def __init__(self) -> None:
        # PostgreSQL
        self.engine: sa.engine.Engine | None = None
        self.SessionLocal: sessionmaker[Session] | None = None

        # Neo4j
        self.neo4j_driver = None

        # Qdrant
        self.qdrant_client: QdrantClient | None = None

        # Redis
        self.redis_client: redis.Redis | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        """Open connections to all configured databases.

        Each connection is independent — a failure in one does **not**
        prevent the others from initialising.
        """
        self._connect_postgres()
        self._connect_neo4j()
        self._connect_qdrant()
        self._connect_redis()

    async def shutdown(self) -> None:
        """Gracefully close every active database connection."""
        if self.engine is not None:
            self.engine.dispose()
            logger.info("PostgreSQL connection closed.")

        if self.neo4j_driver is not None:
            self.neo4j_driver.close()
            logger.info("Neo4j connection closed.")

        if self.qdrant_client is not None:
            self.qdrant_client.close()
            logger.info("Qdrant connection closed.")

        if self.redis_client is not None:
            self.redis_client.close()
            logger.info("Redis connection closed.")

    # ------------------------------------------------------------------
    # Private helpers — one per backend
    # ------------------------------------------------------------------

    def _connect_postgres(self) -> None:
        """Create a synchronous SQLAlchemy engine + session factory."""
        try:
            self.engine = sa.create_engine(
                settings.postgres_dsn,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=settings.debug,
            )
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
            # Quick connectivity check
            with self.engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            logger.info("PostgreSQL connected — %s", settings.postgres_dsn)
        except Exception as exc:
            logger.warning("PostgreSQL unavailable: %s", exc)
            self.engine = None
            self.SessionLocal = None

    def _connect_neo4j(self) -> None:
        """Create a Neo4j bolt driver."""
        try:
            self.neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            self.neo4j_driver.verify_connectivity()
            logger.info("Neo4j connected — %s", settings.neo4j_uri)
        except Exception as exc:
            logger.warning("Neo4j unavailable: %s", exc)
            self.neo4j_driver = None

    def _connect_qdrant(self) -> None:
        """Create a Qdrant HTTP client."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            # Quick connectivity check — list existing collections
            self.qdrant_client.get_collections()
            logger.info(
                "Qdrant connected — %s:%s",
                settings.qdrant_host,
                settings.qdrant_port,
            )
        except Exception as exc:
            logger.warning("Qdrant unavailable: %s", exc)
            self.qdrant_client = None

    def _connect_redis(self) -> None:
        """Create a Redis client."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info(
                "Redis connected — %s:%s",
                settings.redis_host,
                settings.redis_port,
            )
        except Exception as exc:
            logger.warning("Redis unavailable: %s", exc)
            self.redis_client = None

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def get_db_session(self) -> Generator[Session, None, None]:
        """Yield a SQLAlchemy session, ensuring it is closed after use."""
        if self.SessionLocal is None:
            raise RuntimeError("PostgreSQL is not connected.")
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def get_neo4j_session(self):
        """Return a new Neo4j session (caller must close it)."""
        if self.neo4j_driver is None:
            raise RuntimeError("Neo4j is not connected.")
        return self.neo4j_driver.session()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
db_manager = DatabaseManager()


# ---------------------------------------------------------------------------
# FastAPI dependency functions
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a PostgreSQL SQLAlchemy session."""
    yield from db_manager.get_db_session()


def get_neo4j():
    """FastAPI dependency — returns a Neo4j session."""
    return db_manager.get_neo4j_session()


def get_qdrant() -> QdrantClient | None:
    """FastAPI dependency — returns the shared Qdrant client."""
    return db_manager.qdrant_client


def get_redis() -> redis.Redis | None:
    """FastAPI dependency — returns the shared Redis client."""
    return db_manager.redis_client
