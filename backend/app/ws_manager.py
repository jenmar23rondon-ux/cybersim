"""In-process pub/sub that fans out attack log events to WebSocket clients."""

from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        # correlation_id -> set of sockets subscribed to that run
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        # sockets that want every event (global dashboard feed)
        self._global: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, correlation_id: str | None = None) -> None:
        await ws.accept()
        async with self._lock:
            if correlation_id:
                self._rooms[correlation_id].add(ws)
            else:
                self._global.add(ws)

    async def disconnect(self, ws: WebSocket, correlation_id: str | None = None) -> None:
        async with self._lock:
            if correlation_id:
                self._rooms[correlation_id].discard(ws)
            else:
                self._global.discard(ws)

    async def broadcast(self, correlation_id: str, payload: dict) -> None:
        async with self._lock:
            targets = list(self._rooms.get(correlation_id, set())) + list(self._global)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._rooms.get(correlation_id, set()).discard(ws)
                    self._global.discard(ws)


manager = WebSocketManager()
