from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from src.database import DBSession
from src.models import Post

router = APIRouter(prefix='/posts', tags=['Posts'])


# Schemas


class PostBase(BaseModel):
    cover_url: str | None = None
    credit: str | None = None
    status: str | None = None
    sale_url: str | None = None


class PostCreate(PostBase):
    title: str
    content: str
    author_id: int


class PostUpdate(PostBase):
    title: str | None = None
    content: str | None = None


class PostResponse(PostBase):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# CRUD operations


def create_post(db: DBSession, payload: PostCreate) -> Post:
    new_post = Post(
        title=payload.title,
        content=payload.content,
        author_id=payload.author_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def get_post_by_id(db: DBSession, post_id: int) -> Post | None:
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts_by_author_id(db: DBSession, author_id: int) -> list[Post]:
    return db.query(Post).filter(Post.author_id == author_id).all()


def get_posts(db: DBSession, skip: int = 0, limit: int = 100) -> list[Post]:
    return db.query(Post).offset(skip).limit(limit).all()


def update_post_by_id(
    db: DBSession, post_id: int, post_update: PostUpdate
) -> Post | None:
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        return None
    data = post_update.model_dump(exclude_unset=True)
    blocked_fields = {
        'id',
        'author_id',
        'created_at',
        'updated_at',
    }
    for f in blocked_fields:
        data.pop(f, None)

    for field in list(data.keys()):
        if not hasattr(db_post, field):
            data.pop(field)
    for field, value in data.items():
        setattr(db_post, field, value)

    try:
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post
    except Exception:
        db.rollback()
        raise


def delete_post_by_id(db: DBSession, post_id: int) -> bool:
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        return False

    db.delete(db_post)
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


# Routes
@router.post(
    '/',
    response_model=PostResponse,
    status_code=201,
)
def create_new_post(post: PostCreate, db: DBSession):
    db_post = create_post(db, post)
    return db_post


@router.get(
    '/{post_id}',
    response_model=PostResponse,
    status_code=200,
)
def read_post(post_id: int, db: DBSession):
    db_post = get_post_by_id(db, post_id)
    return db_post


@router.get(
    '/',
    response_model=list[PostResponse],
    status_code=200,
)
def read_posts(db: DBSession, skip: int = 0, limit: int = 10):
    posts = get_posts(db, skip=skip, limit=limit)
    return posts


@router.get(
    '/posts/{author_id}',
    response_model=list[PostResponse],
    status_code=200,
)
def read_posts_by_author(author_id: int, db: DBSession):
    posts = get_posts_by_author_id(db, author_id)
    return posts


@router.patch(
    '/{post_id}',
    response_model=PostResponse,
    status_code=200,
)
def update_post(post_id: int, post_update: PostUpdate, db: DBSession):
    db_post = update_post_by_id(db, post_id, post_update)
    if not db_post:
        raise HTTPException(status_code=404, detail='Post not found')
    return db_post


@router.delete('/{post_id}', status_code=204)
def delete_post(post_id: int, db: DBSession):
    if not delete_post_by_id(db, post_id):
        raise HTTPException(status_code=404, detail='Post not found')
    return None
