from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func

from src.database import DBSession
from src.models import Author, Notification, NotificationRecipient, Post, PostReport, User, session
from src.notification_manager import manager

router = APIRouter(prefix='/reports', tags=['Reports'])

# schemas


class RepostBase(BaseModel):
    created_at: datetime
    updated_at: datetime


class ReportResponse(RepostBase):
    id: int
    user_id: int
    post_id: int
    reason: str
    status: str

    # Config for ORM mode
    model_config = ConfigDict(from_attributes=True)


# CRUD


def get_id_user_by_token(db: DBSession, Stoken: str) -> int | None:
    try:
        sessions = (
            db.query(session)
            .filter(session.token == Stoken, session.expires_at > func.now())
            .first()
        )
        if sessions is None:
            return None
        return sessions.user_id
    except Exception:
        return None


def check_admin_by_token(db: DBSession, Stoken: str) -> bool:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return False
        user = db.query(User).filter(User.id == id_user).first()
        if user is None:
            return False
        return user.role == 2
    except Exception:
        return False


def get_reports_by_post_id(db: DBSession, post_id: int):
    reports = db.query(PostReport).filter(PostReport.post_id == post_id).all()
    return reports


def get_all_report_by_status(db: DBSession, status: str):
    reports = db.query(PostReport).filter(PostReport.status == status).all()
    return reports


async def create_report(db: DBSession, token: str, post_id: int, reason: str):
    try:
        user_id = get_id_user_by_token(db, token)
        if user_id is None:
            return 'Invalid or expired session token'
        new_report = PostReport(
            post_id=post_id,
            user_id=user_id,
            reason=reason,
            status='PENDING',
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        try:
            # gui thong bao den chu post
            post = db.query(Post).filter(Post.id == post_id).first()
            if post:
                title = 'Your post has been reported'
                message = (
                    f'Your post titled "{post.title}" has been reported '
                    f'for the following reason: {reason}. '
                    'Our team will review it shortly.'
                )
                # tao notification
                notification = Notification(
                    title=title,
                    message=message,
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                # tao notification recipient
                # lay author_id de lay user_id
                author = db.query(Author).filter(Author.id == post.author_id).first()
                payload = {'title': title, 'message': message}
                if author:
                    notification_recipient = NotificationRecipient(
                        notification_id=notification.id,
                        user_id=author.user_id,
                    )
                    db.add(notification_recipient)
                    db.commit()
                    db.refresh(notification_recipient)
                    # websocket real-time notification can be sent here
                    await manager.send_notification(author.user_id, payload)
                # gui tat ca cac admin
                admins = db.query(User).filter(User.role == 2).all()
                for admin in admins:
                    notification_recipient_admin = NotificationRecipient(
                        notification_id=notification.id,
                        user_id=admin.id,
                    )
                    db.add(notification_recipient_admin)
                    db.commit()
                    db.refresh(notification_recipient_admin)
                    await manager.send_notification(admin.id, payload)
        except Exception as e:
            db.rollback()
            print(f'Error creating notification for report: {str(e)}')
        return new_report
    except Exception as e:
        db.rollback()
        return f'Error creating report: {str(e)}'


def approve_report(db: DBSession, report_id: int, token: str) -> str:
    try:
        if not check_admin_by_token(db, token):
            return 'User is not authorized to approve reports'
        report = db.query(PostReport).filter(PostReport.id == report_id).first()
        if report is None:
            return 'Report not found'
        post = db.query(Post).filter(Post.id == report.post_id).first()
        if post is None:
            return 'Post not found'
        db.delete(post)
        db.commit()
        report.status = 'APPROVED'
        db.commit()
        db.refresh(report)
        return 'Report approved and post deleted successfully'
    except Exception as e:
        db.rollback()
        raise e


def reject_report(db: DBSession, report_id: int, token: str) -> str:
    try:
        if not check_admin_by_token(db, token):
            return 'User is not authorized to reject reports'
        report = db.query(PostReport).filter(PostReport.id == report_id).first()
        if report:
            report.status = 'REJECTED'
            db.commit()
            db.refresh(report)
        return 'Report rejected successfully'
    except Exception as e:
        db.rollback()
        raise e


def delete_report(db: DBSession, report_id: int, token: str) -> str:
    try:
        if not check_admin_by_token(db, token):
            return 'User is not authorized to delete reports'
        report = db.query(PostReport).filter(PostReport.id == report_id).first()
        if report:
            db.delete(report)
            db.commit()
        return 'Report deleted successfully'
    except Exception as e:
        db.rollback()
        raise e


# Routes
@router.get('/post/{post_id}', response_model=list[ReportResponse])
def api_get_reports_by_post_id(post_id: int, db: DBSession):
    reports = get_reports_by_post_id(db, post_id)
    return reports


@router.get('/status/{status}', response_model=list[ReportResponse])
def api_get_all_report_by_status(status: str, db: DBSession):
    reports = get_all_report_by_status(db, status)
    return reports


@router.post('/create', response_model=ReportResponse)
async def api_create_report(token: str, post_id: int, reason: str, db: DBSession):
    report = await create_report(db, token, post_id, reason)
    return report


@router.patch('/{report_id}/approve', response_model=str)
def api_approve_report(report_id: int, token: str, db: DBSession):
    return approve_report(db, report_id, token)


@router.patch('/{report_id}/reject', response_model=str)
def api_reject_report(report_id: int, token: str, db: DBSession):
    return reject_report(db, report_id, token)


@router.delete('/{report_id}/delete', response_model=str)
def api_delete_report(report_id: int, token: str, db: DBSession):
    return delete_report(db, report_id, token)
