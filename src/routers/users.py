from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from src.database import DBSession
from src.models import User

router = APIRouter(prefix='/users')


# Schemas
class UserBase(BaseModel):
    email: str
    phone_number: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # ORM mode
    model_config = ConfigDict(from_attributes=True)


# CRUD operations
def create_user(db: DBSession, user: UserCreate) -> User:
    new_user = User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(db: DBSession, id: int) -> User | None:
    return db.query(User).filter(User.id == id).first()


def get_users(db: DBSession, skip: int = 0, limit: int = 10) -> list[User]:
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# Routes
@router.post('/', response_model=UserResponse, status_code=201, tags=['Users'])
def create_new_user(user: UserCreate, db: DBSession):
    db_user = create_user(db, user)
    return db_user


@router.get(
    '/{id}', response_model=UserResponse, status_code=200, tags=['Users']
)
def read_user(id: int, db: DBSession):
    db_user = get_user_by_id(db, id)
    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')

    return db_user


@router.get(
    '/', response_model=list[UserResponse], status_code=200, tags=['Users']
)
def read_users(db: DBSession, skip: int = 0, limit: int = 10):
    users = get_users(db, skip=skip, limit=limit)
    return users
