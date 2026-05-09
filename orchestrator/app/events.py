from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

from app.models import PipelineEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Broadcast pipeline events to all connected WebSocket clients.

    Uses an async queue so emit() never blocks the pipeline.
    A background task drains the queue and sends to clients.
    """

    def __init__(self):
        self._clients: list[WebSocket] = []
        self._history: list[PipelineEvent] = []
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._drain_task: asyncio.Task | None = None

    def _ensure_drain_task(self):
        if self._drain_task is None or self._drain_task.done():
            self._drain_task = asyncio.create_task(self._drain_loop())

    async def _drain_loop(self):
        """Background task that sends queued messages to all clients."""
        while True:
            message = await self._queue.get()
            dead: list[WebSocket] = []
            for client in self._clients:
                try:
                    await asyncio.wait_for(client.send_text(message), timeout=2.0)
                except (asyncio.TimeoutError, Exception):
                    dead.append(client)
            for client in dead:
                self._clients.remove(client)
            self._queue.task_done()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.append(ws)
        self._ensure_drain_task()
        logger.info("WebSocket client connected (%d total)", len(self._clients))

        # Send event history so late-joining clients catch up
        for event in self._history:
            try:
                await ws.send_text(event.model_dump_json())
            except Exception:
                break

    async def disconnect(self, ws: WebSocket) -> None:
        if ws in self._clients:
            self._clients.remove(ws)
        logger.info("WebSocket client disconnected (%d remaining)", len(self._clients))

    async def emit(self, event: PipelineEvent) -> None:
        """Queue an event for broadcast. Returns immediately."""
        self._history.append(event)
        self._ensure_drain_task()
        self._queue.put_nowait(event.model_dump_json())

    def clear_history(self) -> None:
        self._history.clear()

    @property
    def client_count(self) -> int:
        return len(self._clients)
