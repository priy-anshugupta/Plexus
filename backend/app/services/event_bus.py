#!/usr/bin/env python3
"""
Plexus Backend — Scan Event Bus

Publishes and subscribes to real-time scan progress events.
Uses Redis pub/sub when available; falls back to in-memory asyncio Queues.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from app.core.database import db_manager

logger = logging.getLogger(__name__)

# In-memory fallback queue registry
_memory_queues: dict[str, asyncio.Queue] = {}


class ScanEventBus:
    """Event bus for streaming scan progress updates."""

    def __init__(self) -> None:
        self._redis = db_manager.redis_client

    async def publish(self, scan_id: str, event: dict) -> None:
        """Publish a scan progress event."""
        payload = json.dumps({"scan_id": scan_id, **event})
        redis_available = False
        if self._redis:
            try:
                # Use a thread pool or just try-catch since ping() is fast
                self._redis.ping()
                redis_available = True
            except Exception:
                redis_available = False
        if redis_available:
            try:
                self._redis.publish(f"scan:{scan_id}", payload)
                return
            except Exception as exc:
                logger.warning("Redis publish failed, falling back to memory: %s", exc)
        # Fallback: in-memory queue
        queue = _memory_queues.get(scan_id)
        if queue:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, scan_id: str) -> AsyncGenerator[str, None]:
        """Yield SSE-formatted events for a scan until completion."""
        redis_available = False
        if self._redis:
            try:
                self._redis.ping()
                redis_available = True
            except Exception:
                redis_available = False
        if redis_available:
            try:
                pubsub = self._redis.pubsub()
                pubsub.subscribe(f"scan:{scan_id}")
                for message in pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        yield f"data: {data}\n\n"
                        # Stop if scan completed/failed/cancelled
                        try:
                            payload = json.loads(data)
                            if payload.get("event") in ("completed", "failed", "cancelled"):
                                break
                        except Exception:
                            pass
                pubsub.close()
                return
            except Exception as exc:
                logger.warning("Redis subscribe failed, falling back to memory: %s", exc)

        # Fallback: in-memory queue
        queue = asyncio.Queue(maxsize=100)
        _memory_queues[scan_id] = queue
        try:
            while True:
                payload = await asyncio.wait_for(queue.get(), timeout=300.0)
                yield f"data: {payload}\n\n"
                try:
                    event_data = json.loads(payload)
                    if event_data.get("event") in ("completed", "failed", "cancelled"):
                        break
                except Exception:
                    pass
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'event': 'timeout', 'message': 'Scan stream timed out'})}\n\n"
        finally:
            _memory_queues.pop(scan_id, None)


# Singleton
scan_event_bus = ScanEventBus()
