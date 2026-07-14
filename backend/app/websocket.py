from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    """
    Tracks live WebSocket subscribers.

    Two channels:
      * per-endpoint — keyed by endpoint id. Subscribing requires knowing the
        endpoint's (unguessable) id, so it is capability-scoped.
      * global — keyed by workspace id. A client only receives readings for
        endpoints in the workspace it subscribed to, so live data never leaks
        across workspaces.
    """

    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
        self._global: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, endpoint_id: str):
        await websocket.accept()
        self.connections.setdefault(endpoint_id, []).append(websocket)

    async def connect_global(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        self._global.setdefault(workspace_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, endpoint_id: str):
        try:
            self.connections.get(endpoint_id, []).remove(websocket)
        except ValueError:
            pass

    def disconnect_global(self, websocket: WebSocket, workspace_id: str):
        try:
            self._global.get(workspace_id, []).remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: dict, endpoint_id: str, workspace_id: str):
        # Per-endpoint subscribers (they already hold the endpoint id).
        dead = []
        for ws in self.connections.get(endpoint_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, endpoint_id)

        # Global subscribers of THIS workspace only.
        dead_g = []
        for ws in self._global.get(workspace_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead_g.append(ws)
        for ws in dead_g:
            self.disconnect_global(ws, workspace_id)


manager = ConnectionManager()
