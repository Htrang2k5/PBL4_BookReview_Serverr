from fastapi import APIRouter
from sqlalchemy import func

from src.database import DBSession
from src.models import Author, Notification, NotificationRecipient, Post, Reaction, session
from src.notification_manager import manager

router = APIRouter(prefix='/reactions', tags=['Reactions'])


# CRUD
def get_reactions_by_post_id(db: DBSession, post_id: int):
    reactions = db.query(Reaction).filter(Reaction.post_id == post_id).all()
    return reactions


def get_reactions_by_post_id_and_token(db: DBSession, post_id: int, Stoken: str) -> str:
    id_user = get_id_user_by_token(db, Stoken)
    if id_user is None:
        return 'Invalid or expired session token'
    reactions = (
        db.query(Reaction).filter(Reaction.post_id == post_id, Reaction.user_id == id_user).first()
    )
    return reactions.type


def get_count_reactions_by_type_and_post_id(db: DBSession, post_id: int, reaction_type: str) -> int:
    count = (
        db.query(Reaction)
        .filter(Reaction.post_id == post_id, Reaction.type == reaction_type)
        .count()
    )
    return count


def get_id_user_by_token(db: DBSession, Stoken: str) -> int | None:
    sessions = (
        db.query(session).filter(session.token == Stoken, session.expires_at > func.now()).first()
    )
    if sessions is None:
        return None
    return sessions.user_id


async def create_reaction(db: DBSession, post_id: int, Stoken: str, reaction_type: str) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'

        check = (
            db.query(Reaction)
            .filter(
                Reaction.post_id == post_id,
                Reaction.user_id == id_user,
                Reaction.type == reaction_type,
            )
            .first()
        )
        if check is not None:
            return 'User has already reacted to this post.'
        check = (
            db.query(Reaction)
            .filter(Reaction.post_id == post_id, Reaction.user_id == id_user)
            .first()
        )
        if check is not None:
            db.delete(check)
            db.commit()

        new_reaction = Reaction(
            post_id=post_id,
            user_id=id_user,
            type=reaction_type,
        )
        db.add(new_reaction)
        db.commit()
        # thong bao neu no la lile
        if reaction_type == 'LIKE':
            try:
                notification = Notification(
                    title='You have a new like notification',
                    message=f'Your post with ID {post_id} has received a new like your post.',
                )
                db.add(notification)
                db.commit()
                db.refresh(notification)
                # lay post_id de lay author_id roi lay user_id
                post = db.query(Post).filter(Post.id == post_id).first()
                author = db.query(Author).filter(Author.id == post.author_id).first()

                notification_recipient = NotificationRecipient(
                    notification_id=notification.id,
                    user_id=author.user_id,
                )
                db.add(notification_recipient)
                db.commit()
                db.refresh(notification_recipient)
                # websocket real-time notification can be sent here
                payload_ws = {
                    'type': 'New Like Received',
                    'message': f'Your post with ID {post_id} has received a new like.',
                }
                await manager.send_notification(author.user_id, payload_ws)
            except Exception as e:
                db.rollback()
                print(f'Error creating notification for new like: {str(e)}')
        return 'Reaction created successfully'
    except Exception as e:
        db.rollback()
        return f'Error creating reaction: {str(e)}'


def delete_reaction(db: DBSession, reaction_id: int, Stoken: str) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        reaction = db.query(Reaction).filter(Reaction.id == reaction_id).first()
        if reaction is None:
            return 'Reaction not found'
        if reaction.user_id != id_user:
            return 'User is not authorized to delete this reaction'
        db.delete(reaction)
        db.commit()
        return 'Reaction deleted successfully'
    except Exception as e:
        db.rollback()
        return f'Error deleting reaction: {str(e)}'


def get_all_like_posts_by_token(db: DBSession, token: str) -> list[int]:
    id_user = get_id_user_by_token(db, token)
    if id_user is None:
        return []
    reactions = (
        db.query(Reaction).filter(Reaction.user_id == id_user, Reaction.type == 'LIKE').all()
    )
    return [reaction.post_id for reaction in reactions]


def get_type_reaction_by_post_id_and_token(db: DBSession, post_id: int, Stoken: str) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        reactions = (
            db.query(Reaction)
            .filter(Reaction.post_id == post_id, Reaction.user_id == id_user)
            .first()
        )
        if reactions is None:
            return 'No reaction found for this post by the user'
        return reactions.type
    except Exception as e:
        return f'Error retrieving reaction type: {str(e)}'


# routers
@router.get('/post/{post_id}')
def api_get_reactions_by_post_id(post_id: int, db: DBSession):
    return get_reactions_by_post_id(db, post_id)


@router.get('/post/{post_id}/count/{reaction_type}')
def api_get_count_reactions_by_type_and_post_id(post_id: int, reaction_type: str, db: DBSession):
    return get_count_reactions_by_type_and_post_id(db, post_id, reaction_type)


@router.post('/post/{post_id}', response_model=str, status_code=201)
async def api_create_reaction(post_id: int, session_token: str, reaction_type: str, db: DBSession):
    return await create_reaction(db, post_id, session_token, reaction_type)


@router.delete('/{reaction_id}', response_model=str)
def api_delete_reaction(reaction_id: int, session_token: str, db: DBSession):
    return delete_reaction(db, reaction_id, session_token)


@router.get('/post/{post_id}/status', response_model=str)
def api_get_reactions_by_post_id_and_token(post_id: int, session_token: str, db: DBSession):
    return get_reactions_by_post_id_and_token(db, post_id, session_token)


@router.get('/user/{user_id}/likes', response_model=list[int])
def api_get_all_like_posts_by_user_id(session_token: str, db: DBSession):
    return get_all_like_posts_by_token(db, session_token)


@router.get('/post/{post_id}/type', response_model=str)
def api_get_type_reaction_by_post_id_and_token(post_id: int, session_token: str, db: DBSession):
    return get_type_reaction_by_post_id_and_token(db, post_id, session_token)
