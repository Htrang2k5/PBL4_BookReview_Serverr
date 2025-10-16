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


class AuthorResponse(BaseModel):
    id: int
    pen_name: str
    profile: UserResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# CRUD operations
def create_author_with_user(db: DBSession, payload: AuthorCreate) -> Author:
    try:
        # Create the user profile first
        user_data = payload.profile
        new_user = User(
            email=user_data.email,
            password=user_data.password,
            phone_number=user_data.phone_number,
        )
        db.add(new_user)
        db.flush()

        # Create the author linked to the user
        new_author = Author(pen_name=payload.pen_name, user_id=new_user.id)

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

        raise HTTPException(status_code=400, detail=message)


# Routes
@router.post(
    '/', response_model=AuthorResponse, status_code=201, tags=['Authors']
)
def create_new_author(author: AuthorCreate, db: DBSession):
    db_author = create_author_with_user(db, author)
    return db_author
