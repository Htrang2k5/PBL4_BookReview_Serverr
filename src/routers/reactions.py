from fastapi import APIRouter
from sqlalchemy import func

from src.database import DBSession
from src.models import Reaction, session

router = APIRouter(prefix='/reactions', tags=['Reactions'])


# CRUD
def get_reactions_by_post_id(db: DBSession, post_id: int):
    reactions = db.query(Reaction).filter(Reaction.post_id == post_id).all()
    return reactions


def get_reactions_by_post_id_and_token(
    db: DBSession, post_id: int, Stoken: str
) -> str:
    id_user = get_id_user_by_token(db, Stoken)
    if id_user is None:
        return 'Invalid or expired session token'
    reactions = (
        db.query(Reaction)
        .filter(Reaction.post_id == post_id, Reaction.user_id == id_user)
        .first()
    )
    return reactions.type


def get_count_reactions_by_type_and_post_id(
    db: DBSession, post_id: int, reaction_type: str
) -> int:
    count = (
        db.query(Reaction)
        .filter(Reaction.post_id == post_id, Reaction.type == reaction_type)
        .count()
    )
    return count


def get_id_user_by_token(db: DBSession, Stoken: str) -> int | None:
    sessions = (
        db.query(session)
        .filter(session.token == Stoken, session.expires_at > func.now())
        .first()
    )
    if sessions is None:
        return None
    return sessions.user_id


def create_reaction(
    db: DBSession, post_id: int, Stoken: str, reaction_type: str
) -> str:
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
        db.query(Reaction)
        .filter(Reaction.user_id == id_user, Reaction.type == 'LIKE')
        .all()
    )
    return [reaction.post_id for reaction in reactions]


def get_type_reaction_by_post_id_and_token(
    db: DBSession, post_id: int, Stoken: str
) -> str:
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
async def api_get_reactions_by_post_id(post_id: int, db: DBSession):
    return get_reactions_by_post_id(db, post_id)


@router.get('/post/{post_id}/count/{reaction_type}')
async def api_get_count_reactions_by_type_and_post_id(
    post_id: int, reaction_type: str, db: DBSession
):
    return get_count_reactions_by_type_and_post_id(db, post_id, reaction_type)


@router.post('/post/{post_id}', response_model=str, status_code=201)
async def api_create_reaction(
    post_id: int, session_token: str, reaction_type: str, db: DBSession
):
    return create_reaction(db, post_id, session_token, reaction_type)


@router.delete('/{reaction_id}', response_model=str)
async def api_delete_reaction(
    reaction_id: int, session_token: str, db: DBSession
):
    return delete_reaction(db, reaction_id, session_token)


@router.get('/post/{post_id}/status', response_model=str)
async def api_get_reactions_by_post_id_and_token(
    post_id: int, session_token: str, db: DBSession
):
    return get_reactions_by_post_id_and_token(db, post_id, session_token)


@router.get('/user/{user_id}/likes', response_model=list[int])
async def api_get_all_like_posts_by_user_id(session_token: str, db: DBSession):
    return get_all_like_posts_by_token(db, session_token)


@router.get('/post/{post_id}/type', response_model=str)
async def api_get_type_reaction_by_post_id_and_token(
    post_id: int, session_token: str, db: DBSession
):
    return get_type_reaction_by_post_id_and_token(db, post_id, session_token)
