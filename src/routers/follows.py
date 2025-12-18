from fastapi import APIRouter
from sqlalchemy import func, select

from src.database import DBSession
from src.models import (
    Author,
    Notification,
    NotificationRecipient,
    session,
    users_follow_authors,
)
from src.notification_manager import manager

router = APIRouter(prefix='/follows', tags=['Follows'])


# CRUD


def get_id_user_by_token(db: DBSession, Stoken: str) -> int | None:
    sessions = (
        db.query(session)
        .filter(session.token == Stoken, session.expires_at > func.now())
        .first()
    )
    if sessions is None:
        return None
    return sessions.user_id


def get_all_follow_users_by_author_id(db: DBSession, author_id: int):
    follows = db.execute(
        select(users_follow_authors.c.user_id).where(
            users_follow_authors.c.author_id == author_id
        )
    ).all()
    return [follow.user_id for follow in follows]


def get_all_follower_authors_by_user_id(db: DBSession, user_id: int):
    follows = db.execute(
        select(users_follow_authors.c.author_id).where(
            users_follow_authors.c.user_id == user_id
        )
    ).all()
    return [follow.author_id for follow in follows]


def check_status_follow_by_token_and_authorId(
    db: DBSession, Stoken: str, id_author: int
):
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        follow = db.execute(
            select(users_follow_authors).where(
                users_follow_authors.c.user_id == id_user,
                users_follow_authors.c.author_id == id_author,
            )
        ).first()
        if follow is None:
            return 'User is not following this author'
        return 'User is following this author'
    except Exception as e:
        return f'Error validating session token: {str(e)}'


async def follow_author_by_token_of_userId(
    db: DBSession, Stoken: str, id_author: int
):
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        author = db.query(Author).filter(Author.id == id_author).first()
        if author is None:
            return 'Author does not exist'
        if id_user == author.user_id:
            return 'User cannot follow themselves'
        follow = db.execute(
            select(users_follow_authors).where(
                users_follow_authors.c.user_id == id_user,
                users_follow_authors.c.author_id == id_author,
            )
        ).first()
        if follow is not None:
            return 'User is already following this author'
        new_follow = users_follow_authors.insert().values(
            user_id=id_user, author_id=id_author
        )
        db.execute(new_follow)
        db.commit()
        # Create a notification for the author
        notification = Notification(
            title='You have a new follower!',
            message=f'User {id_user} has started following you.',
        )
        db.add(notification)
        db.commit()
        # Add the notification recipient
        notification_recipient = NotificationRecipient(
            notification_id=notification.id, user_id=author.user_id
        )
        db.add(notification_recipient)
        db.commit()
        # Send real-time notification if the author is connected
        payload = {
            'type': 'NEW_FOLLOWER',
            'message': f'User {id_user} is now following you!',
        }
        pushed = await manager.send_notification(author.user_id, payload)
        if pushed:
            print(f'Notification sent to author {id_author}')
        return 'User followed successfully'
    except Exception as e:
        return f'Error validating session token: {str(e)}'


def unfollow_author_by_token_of_userId(
    db: DBSession, Stoken: str, id_author: int
):
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        follow = db.execute(
            select(users_follow_authors).where(
                users_follow_authors.c.user_id == id_user,
                users_follow_authors.c.author_id == id_author,
            )
        ).first()
        if follow is None:
            return 'User is not following this author'
        delete_follow = users_follow_authors.delete().where(
            users_follow_authors.c.user_id == id_user,
            users_follow_authors.c.author_id == id_author,
        )
        db.execute(delete_follow)
        db.commit()
        return 'User unfollowed successfully'
    except Exception as e:
        return f'Error validating session token: {str(e)}'


# router endpoints would go here
@router.post('/', response_model=str, status_code=201)
async def follow_user(session_token: str, author_id: int, db: DBSession):
    try:
        return await follow_author_by_token_of_userId(
            db, session_token, author_id
        )
    except Exception as e:
        return f'Error: {str(e)}'


@router.get('/{author_id}/status', response_model=str)
async def check_follow_status(
    session_token: str, author_id: int, db: DBSession
):
    try:
        return check_status_follow_by_token_and_authorId(
            db, session_token, author_id
        )
    except Exception as e:
        return f'Error: {str(e)}'


@router.get('/{author_id}/followers', response_model=list[int])
async def get_followers(author_id: int, db: DBSession):
    try:
        return get_all_follow_users_by_author_id(db, author_id)
    except Exception as e:
        return f'Error: {str(e)}'


@router.get('/user/{user_id}/following', response_model=list[int])
async def get_following(user_id: int, db: DBSession):
    try:
        return get_all_follower_authors_by_user_id(db, user_id)
    except Exception as e:
        return f'Error: {str(e)}'


@router.delete('/', response_model=str)
async def unfollow_user(session_token: str, author_id: int, db: DBSession):
    try:
        return unfollow_author_by_token_of_userId(db, session_token, author_id)
    except Exception as e:
        return f'Error: {str(e)}'
