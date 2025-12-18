# src/routers/notification_manager.py
from fastapi import WebSocket


class NotificationManager:
    def __init__(self):
        self.active: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        self.active.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active:
            self.active[user_id].discard(websocket)
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_notification(self, user_id: int, payload: dict):
        sockets = list(self.active.get(user_id, []))
        if not sockets:
            return False
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(user_id, ws)
        return True

    def user_is_online(self, user_id: int) -> bool:
        return user_id in self.active and len(self.active[user_id]) > 0


manager = NotificationManager()
