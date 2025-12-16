from fastapi import APIRouter
from sqlalchemy import func

from src.database import DBSession
from src.models import Comment, session

router = APIRouter(prefix='/comments', tags=['Comments'])


# CRUD
def get_comments_by_post_id(db: DBSession, post_id: int):
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return comments


def get_id_user_by_token(db: DBSession, Stoken: str) -> int | None:
    sessions = (
        db.query(session)
        .filter(session.token == Stoken, session.expires_at > func.now())
        .first()
    )
    if sessions is None:
        return None
    return sessions.user_id


def create_comment(
    db: DBSession, post_id: int, Stoken: str, content: str
) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        new_comment = Comment(
            post_id=post_id,
            user_id=id_user,
            content=content,
        )
        db.add(new_comment)
        db.commit()
        return 'Comment created successfully'
    except Exception as e:
        db.rollback()
        return f'Error creating comment: {str(e)}'


def delete_comment(db: DBSession, comment_id: int, Stoken: str) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment is None:
            return 'Comment not found'
        if comment.user_id != id_user:
            return 'User is not authorized to delete this comment'
        db.delete(comment)
        db.commit()
        return 'Comment deleted successfully'
    except Exception as e:
        db.rollback()
        return f'Error deleting comment: {str(e)}'


def update_comment(
    db: DBSession, comment_id: int, Stoken: str, new_content: str
) -> str:
    try:
        id_user = get_id_user_by_token(db, Stoken)
        if id_user is None:
            return 'Invalid or expired session token'
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment is None:
            return 'Comment not found'
        if comment.user_id != id_user:
            return 'User is not authorized to update this comment'
        comment.content = new_content
        db.commit()
        return 'Comment updated successfully'
    except Exception as e:
        db.rollback()
        return f'Error updating comment: {str(e)}'


# router
@router.get('/post/{post_id}')
def api_get_comments_by_post_id(post_id: int, db: DBSession):
    return get_comments_by_post_id(db, post_id)


@router.post('/post/{post_id}/create')
def api_create_comment(post_id: int, Stoken: str, content: str, db: DBSession):
    return create_comment(db, post_id, Stoken, content)


@router.delete('/{comment_id}/delete')
def api_delete_comment(comment_id: int, Stoken: str, db: DBSession):
    return delete_comment(db, comment_id, Stoken)


@router.put('/{comment_id}/update')
def api_update_comment(
    comment_id: int, Stoken: str, new_content: str, db: DBSession
):
    return update_comment(db, comment_id, Stoken, new_content)
