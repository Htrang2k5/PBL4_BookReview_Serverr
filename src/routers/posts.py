import os
import shutil
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from src.database import DBSession
from src.models import (
    Notification,
    NotificationRecipient,
    Post,
    users_follow_authors,
)
from src.notification_manager import manager
from src.selenium_pages import web_data

router = APIRouter(prefix='/posts', tags=['Posts'])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)

UPLOAD_FILE_PARAM = File(...)


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


class PostResponseShort(PostBase):
    id: int
    title: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PostCrawl(PostBase):
    title: str
    content: str
    author_id: int
    credit: str | None = None
    created_at: datetime | None = None


# CRUD operations


def get_all_flowers_of_author(db: DBSession, author_id: int) -> list[int]:
    followers = db.execute(
        users_follow_authors.select().where(users_follow_authors.c.author_id == author_id)
    ).all()
    return [follower.user_id for follower in followers]


def create_post(db: DBSession, payload: PostCreate):
    try:
        new_post = Post(
            title=payload.title,
            content=payload.content,
            author_id=payload.author_id,
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        # create notification for new post
        notification = Notification(
            title='Youe have a new notification of new post',
            message=f'New post titled "{new_post.title}" has been published.',
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        # get all followers of the author
        followers_ids = get_all_flowers_of_author(db, payload.author_id)
        for follower_id in followers_ids:
            notification_recipient = NotificationRecipient(
                notification_id=notification.id,
                user_id=follower_id,
            )
            db.add(notification_recipient)
            db.commit()
            db.refresh(notification_recipient)
        return new_post, new_post.author_id, new_post.title, followers_ids
    except Exception as e:
        db.rollback()
        raise e


def create_post_crawl(db: DBSession, payload: PostCrawl) -> Post:
    post = db.query(Post).filter(Post.title == payload.title).first()
    if post:
        return None
    try:
        new_post = Post(
            title=payload.title,
            content=payload.content,
            credit=payload.credit,
            created_at=payload.created_at,
            author_id=payload.author_id,
            cover_url=payload.cover_url,
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception:
        return None


def get_post_by_id(db: DBSession, post_id: int) -> Post | None:
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts_by_author_id(db: DBSession, author_id: int) -> list[Post]:
    return db.query(Post).filter(Post.author_id == author_id).all()


def get_posts(db: DBSession, skip: int = 0, limit: int = 100) -> list[Post]:
    return db.query(Post).offset(skip).limit(limit).all()


def get_posts_by_keyword(db: DBSession, keyword: str) -> list[Post]:
    return db.query(Post).filter(Post.title.ilike(f'%{keyword}%')).all()


def update_post_by_id(db: DBSession, post_id: int, post_update: PostUpdate) -> Post | None:
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


def edit_save_path(db: DBSession):
    try:
        posts = db.query(Post).all()
        for post in posts:
            if post.cover_url:
                file_name = post.cover_url.split('/')[-1]
                post.cover_url = '/static/images/' + file_name
                db.add(post)
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_post_count(db: DBSession) -> int:
    return db.query(Post).count()


# Routes


@router.post(
    '/',
    response_model=PostResponse,
    status_code=201,
)
async def create_new_post(post: PostCreate, db: DBSession):
    try:
        db_post, author_id, title, follower_ids = create_post(db, post)
        # websocket real-time notification can be sent here
        payload_ws = {
            'type': 'NEW_POST',
            'message': f'Author {author_id} has a new post: {title}',
        }
        for follower_id in follower_ids:
            pushed = await manager.send_notification(follower_id, payload_ws)
            if pushed:
                print(f'Notification sent to follower {follower_id}')
            else: 
                raise HTTPException(
                    status_code=500,
                    detail=f'Could not send notification to follower {follower_id}')
        return db_post
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error creating post: {str(e)}') from e


@router.get('/count', response_model=int, status_code=200)
def count_posts(db: DBSession):
    count = get_post_count(db)
    return count


@router.get(
    '/{post_id}',
    response_model=PostResponse,
    status_code=200,
)
def read_post(post_id: int, db: DBSession):
    try:
        db_post = get_post_by_id(db, post_id)
        if not db_post:
            raise HTTPException(status_code=404, detail='Post not found')
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
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


@router.post(
    '/crawl',
    response_model=str,
    status_code=201,
)
def create_post_from_crawl(month: int, db: DBSession):
    posts = web_data.find_reviews(month)
    for post in posts:
        if len(post[2]) > 65000:
            continue
        post = PostCrawl(
            title=post[1],
            content=post[2],
            author_id=1,
            created_at=post[0],
            credit=post[4],
            cover_url=post[3],
        )
        create_post_crawl(db, post)
    return 'Posts crawled and created successfully'


@router.post(
    '/edit-save-path',
    response_model=str,
    status_code=200,
)
def edit_posts_save_path(db: DBSession):
    edit_save_path(db)
    return 'Posts save paths edited successfully'


@router.get(
    '/search/',
    response_model=list[PostResponseShort],
    status_code=200,
)
def search_posts(keyword: str, db: DBSession):
    posts = get_posts_by_keyword(db, keyword)
    return posts


@router.post(
    '/upload-cover/{post_id}',
    response_model=PostResponse,
    status_code=200,
)
def upload_post_cover_image(post_id: int, db: DBSession, file: UploadFile = UPLOAD_FILE_PARAM):
    # check file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail='Invalid file type. Only images are allowed.',
        )
    db_post = get_post_by_id(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail='Post not found')

    file_name = file.filename.split('/')[-1]
    save_path = os.path.join(IMAGES_DIR, file_name)
    file_url = '/static/images/' + file_name
    try:
        with open(save_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(status_code=500, detail='Could not save cover image') from None
    db_post.cover_url = file_url
    try:
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail='Could not update post cover image') from None
    return db_post


# The End
