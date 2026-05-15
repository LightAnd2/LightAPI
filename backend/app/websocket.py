import asyncio
from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
        self._global: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, endpoint_id: str):
        await websocket.accept()
        if endpoint_id not in self.connections:
            self.connections[endpoint_id] = []
        self.connections[endpoint_id].append(websocket)

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self._global.append(websocket)

    def disconnect(self, websocket: WebSocket, endpoint_id: str):
        if endpoint_id in self.connections:
            try:
                self.connections[endpoint_id].remove(websocket)
            except ValueError:
                pass

    def disconnect_global(self, websocket: WebSocket):
        try:
            self._global.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: dict, endpoint_id: str):
        dead = []
        for ws in self.connections.get(endpoint_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, endpoint_id)

        dead_g = []
        for ws in self._global:
            try:
                await ws.send_json(message)
            except Exception:
                dead_g.append(ws)
        for ws in dead_g:
            self.disconnect_global(ws)


manager = ConnectionManager()
