import contextlib
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func

from src.database import DBSession
from src.models import Notification, NotificationRecipient, session
from src.notification_manager import manager

router = APIRouter(prefix='/notifications', tags=['Notifications'])

# Schemas


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# crud
def get_user_id_by_token(db: DBSession, Stoken: str) -> int | None:
    try:
        sessions = (
            db.query(session)
            .filter(session.token == Stoken, session.expires_at > func.now())
            .first()
        )
        if sessions:
            return sessions.user_id
        return None
    except Exception:
        return None


def get_all_notifications_by_token(db: DBSession, token: str) -> list[NotificationResponse]:
    user_id = get_user_id_by_token(db, token)
    if user_id is None:
        return []
    id_notifications = (
        db.query(NotificationRecipient).filter(NotificationRecipient.user_id == user_id).all()
    )
    notifications = []
    for recipient in id_notifications:
        notification = (
            db.query(Notification).filter(Notification.id == recipient.notification_id).first()
        )
        if notification:
            noti = NotificationResponse(
                id=notification.id,
                title=notification.title,
                message=notification.message,
                is_read=recipient.is_read,
                created_at=notification.created_at,
                updated_at=notification.updated_at,
            )
            notifications.append(noti)
    return notifications


def get_detail_notification_by_token(
    db: DBSession, notification_id: int, token: str
) -> Notification | str:
    try:
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            raise Exception('Invalid or expired session token')
        # danh dau da doc
        notification_recipient = (
            db.query(NotificationRecipient)
            .filter(
                NotificationRecipient.notification_id == notification_id,
                NotificationRecipient.user_id == user_id,
            )
            .first()
        )
        if notification_recipient is None:
            raise Exception('Notification not found for this user')
        notification_recipient.is_read = True
        db.commit()
        # lay chi tiet notification
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        noti = NotificationResponse(id=notification.id,
                                    title=notification.title,
                                    message=notification.message,
                                    is_read=notification_recipient.is_read,
                                    created_at=notification.created_at,
                                    updated_at=notification.updated_at)
        return noti
    except Exception as e:
        return f'Error: {str(e)}'


def mark_notification_as_read(db: DBSession, notification_id: int, token: str) -> str:
    try:
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            return 'Invalid or expired session token'
        notification_recipient = (
            db.query(NotificationRecipient)
            .filter(
                NotificationRecipient.notification_id == notification_id,
                NotificationRecipient.user_id == user_id,
            )
            .first()
        )
        if notification_recipient is None:
            return 'Notification not found for this user'
        notification_recipient.is_read = True
        db.commit()
        return 'Notification marked as read'
    except Exception as e:
        return f'Error: {str(e)}'


def mark_all_notifications_as_read(db: DBSession, token: str) -> str:
    try:
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            return 'Invalid or expired session token'
        notification_recipients = (
            db.query(NotificationRecipient).filter(NotificationRecipient.user_id == user_id).all()
        )
        for recipient in notification_recipients:
            recipient.is_read = True
        db.commit()
        return 'All notifications marked as read'
    except Exception as e:
        return f'Error: {str(e)}'


def mark_notification_as_unread(db: DBSession, notification_id: int, token: str) -> str:
    try:
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            return 'Invalid or expired session token'
        notification_recipient = (
            db.query(NotificationRecipient)
            .filter(
                NotificationRecipient.notification_id == notification_id,
                NotificationRecipient.user_id == user_id,
            )
            .first()
        )
        if notification_recipient is None:
            return 'Notification not found for this user'
        notification_recipient.is_read = False
        db.commit()
        return 'Notification marked as unread'
    except Exception as e:
        return f'Error: {str(e)}'


def mark_all_notifications_as_unread(db: DBSession, token: str) -> str:
    try:
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            return 'Invalid or expired session token'
        notification_recipients = (
            db.query(NotificationRecipient).filter(NotificationRecipient.user_id == user_id).all()
        )
        for recipient in notification_recipients:
            recipient.is_read = False
        db.commit()
        return 'All notifications marked as unread'
    except Exception as e:
        return f'Error: {str(e)}'


# router


@router.websocket('/notifications')
async def websocket_endpoint(websocket: WebSocket, db: DBSession):
    user_id = None
    await websocket.accept()
    try:
        first = await websocket.receive_json()
        token = first.get('token')
        user_id = get_user_id_by_token(db, token)
        if user_id is None:
            await websocket.close(code=1008)
            return
        await manager.connect(user_id, websocket)
        while True:
            await websocket.receive_text()  # keep the connection alive
    except WebSocketDisconnect:
        if user_id is not None:
            manager.disconnect(user_id, websocket)
    except Exception:
        # nếu auth fail hoặc lỗi khác
        with contextlib.suppress(Exception):
            await websocket.close(code=1008)  # policy violation / auth fail


@router.post('/send/{token}', response_model=dict)
async def send_notification_to_user(token: str, db: DBSession):
    user_id = get_user_id_by_token(db, token)
    if user_id is None:
        return {'status': 'invalid token'}
    payload = {'type': 'NEW_NOTIFICATION', 'message': 'Bạn có thông báo mới!'}
    await manager.send_notification(user_id, payload)
    return {'status': 'sent'}


@router.get('/user/notifications', response_model=list[NotificationResponse])
async def api_get_all_notifications_by_token(token: str, db: DBSession):
    notifications = get_all_notifications_by_token(db, token)
    return notifications


@router.get('/notification/{notification_id}', response_model=NotificationResponse | str)
async def api_get_detail_notification_by_token(notification_id: int, token: str, db: DBSession):
    return get_detail_notification_by_token(db, notification_id, token)


@router.post('/notification/{notification_id}/read', response_model=str)
async def api_mark_notification_as_read(notification_id: int, token: str, db: DBSession):
    return mark_notification_as_read(db, notification_id, token)


@router.post('/notifications/read_all', response_model=str)
async def api_mark_all_notifications_as_read(token: str, db: DBSession):
    return mark_all_notifications_as_read(db, token)


@router.post('/notification/{notification_id}/unread', response_model=str)
async def api_mark_notification_as_unread(notification_id: int, token: str, db: DBSession):
    return mark_notification_as_unread(db, notification_id, token)


@router.post('/notifications/unread_all', response_model=str)
async def api_mark_all_notifications_as_unread(token: str, db: DBSession):
    return mark_all_notifications_as_unread(db, token)
