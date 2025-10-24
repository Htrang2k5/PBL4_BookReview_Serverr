from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError

from src.database import DBSession
from src.models import Author, User

from .users import UserCreate, UserResponse

router = APIRouter(prefix='/authors')


# Schemas
class AuthorCreate(BaseModel):
    pen_name: str
    profile: UserCreate
    bio: str | None = None


class AuthorUpdate(BaseModel):
    pen_name: str | None = None
    bio: str | None = None


class AuthorResponse(BaseModel):
    id: int
    pen_name: str
    bio: str | None = None
    profile: UserResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthorCreateByUserId(BaseModel):
    user_id: int
    pen_name: str
    bio: str | None = None


# CRUD operations
def create_author_with_user(db: DBSession, payload: AuthorCreate) -> Author:
    try:
        # Create the user profile first
        user_data = payload.profile
        new_user = User(
            email=user_data.email,
            password=user_data.password,
            phone_number=user_data.phone_number,
            role=1,  # Set role to author
        )
        db.add(new_user)
        db.flush()

        # Create the author linked to the user
        new_author = Author(
            pen_name=payload.pen_name, user_id=new_user.id, bio=payload.bio
        )

        # Establish relationship for response serialization
        new_author.profile = new_user
        db.add(new_author)

        db.commit()
        db.refresh(new_author)
        return new_author
    except IntegrityError as e:
        db.rollback()

        # Determine likely cause for a clearer error message
        message = 'Duplicate or invalid data'
        err_str = str(e.orig).lower() if e.orig else ''
        if 'ix_users_email' in err_str or 'email' in err_str:
            message = 'Email already exists'
        elif 'ix_authors_pen_name' in err_str or 'pen_name' in err_str:
            message = 'Pen name already exists'
        elif 'user_id' in err_str:
            message = 'Author for this user already exists'

        raise HTTPException(status_code=400, detail=message) from e


def create_author_from_userId(
    db: DBSession, author_data: AuthorCreateByUserId
) -> Author:
    try:
        # Update user role to author (role = 1)
        user = db.query(User).filter(User.id == author_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        user.role = 1

        new_author = Author(
            pen_name=author_data.pen_name,
            user_id=author_data.user_id,
            bio=author_data.bio,
        )
        db.add(new_author)
        db.commit()
        db.refresh(new_author)
        return new_author
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail='Duplicate or invalid data'
        ) from e


def delete_author(db: DBSession, author_id: int) -> bool:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail='Author not found')

    db.delete(author)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    return True


def get_author_by_id(db: DBSession, author_id: int) -> Author | None:
    author = db.query(Author).filter(Author.id == author_id).first()
    return author


def get_author_by_user_id(db: DBSession, user_id: int) -> Author | None:
    author = db.query(Author).filter(Author.user_id == user_id).first()
    return author


def get_all_authors(db: DBSession) -> list[Author]:
    authors = db.query(Author).all()
    return authors


def update_author(
    db: DBSession, author_id: int, author_data: AuthorUpdate
) -> Author | None:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail='Author not found')

    # Update author fields
    author.pen_name = (
        author_data.pen_name or author.pen_name
    )  # Update pen_name if provided
    author.bio = author_data.bio or author.bio  # Update bio if provided
    try:
        db.commit()
        db.refresh(author)
        return author
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail='Duplicate or invalid data'
        ) from e


# Routes
@router.post(
    '/', response_model=AuthorResponse, status_code=201, tags=['Authors']
)
def create_new_author(author: AuthorCreate, db: DBSession):
    db_author = create_author_with_user(db, author)
    return db_author


@router.delete('/{author_id}', status_code=204, tags=['Authors'])
def delete_author_by_id(author_id: int, db: DBSession):
    delete_author(db, author_id)
    return None


@router.post(
    '/{user_id}',
    response_model=AuthorResponse,
    status_code=201,
    tags=['Authors'],
)
def create_new_author_by_user_id(author: AuthorCreateByUserId, db: DBSession):
    db_author = create_author_from_userId(db, author)
    return db_author


@router.get(
    '/{author_id}',
    response_model=AuthorResponse,
    status_code=200,
    tags=['Authors'],
)
def read_author_by_author_id(author_id: int, db: DBSession):
    db_author = get_author_by_id(db, author_id)
    if not db_author:
        raise HTTPException(status_code=404, detail='Author not found')
    return db_author


@router.get(
    '/', response_model=list[AuthorResponse], status_code=200, tags=['Authors']
)
def read_all_authors(db: DBSession):
    authors = get_all_authors(db)
    return authors


@router.get(
    '/user/{user_id}',
    response_model=AuthorResponse,
    status_code=200,
    tags=['Authors'],
)
def read_author_by_user_id(user_id: int, db: DBSession):
    db_author = get_author_by_user_id(db, user_id)
    if not db_author:
        raise HTTPException(status_code=404, detail='Author not found')
    return db_author


@router.patch(
    '/{author_id}',
    response_model=AuthorResponse,
    status_code=200,
    tags=['Authors'],
)
def update_author_by_id(
    author_id: int, author_data: AuthorUpdate, db: DBSession
):
    db_author = update_author(db, author_id, author_data)
    return db_author
