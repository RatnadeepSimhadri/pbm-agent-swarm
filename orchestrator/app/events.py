from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket
from pydantic import BaseModel

from app.models import PipelineEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Broadcast pipeline events to all connected WebSocket clients."""

    def __init__(self):
        self._clients: list[WebSocket] = []
        self._history: list[PipelineEvent] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.append(ws)
        logger.info("WebSocket client connected (%d total)", len(self._clients))

        # Send event history so late-joining clients catch up
        for event in self._history:
            try:
                await ws.send_text(event.model_dump_json())
            except Exception:
                break

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._clients:
                self._clients.remove(ws)
        logger.info("WebSocket client disconnected (%d remaining)", len(self._clients))

    async def emit(self, event: PipelineEvent) -> None:
        """Broadcast an event to all connected clients."""
        self._history.append(event)
        message = event.model_dump_json()

        async with self._lock:
            dead: list[WebSocket] = []
            for client in self._clients:
                try:
                    await client.send_text(message)
                except Exception:
                    dead.append(client)
            for client in dead:
                self._clients.remove(client)

    def clear_history(self) -> None:
        self._history.clear()

    @property
    def client_count(self) -> int:
        return len(self._clients)
