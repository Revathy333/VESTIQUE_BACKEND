from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Maps user_id → active WebSocket
        self.active: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active.pop(user_id, None)

    async def send_to(self, user_id: int, data: dict):
        ws = self.active.get(user_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(user_id)

    def is_connected(self, user_id: int) -> bool:
        return user_id in self.active


# Global singleton
manager = ConnectionManager()