import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.exc import IntegrityError

from src.constants import Regex
from src.database import DBSession
from src.models import Author, User

router = APIRouter(prefix='/users')


# Schemas
class UserBase(BaseModel):
    email: str
    phone_number: str | None = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not isinstance(v, str):
            raise ValueError('Invalid email address')

        v = v.strip()
        email_regex = re.compile(Regex.EMAIL_REGEX)
        if not email_regex.match(v):
            raise ValueError('Invalid email address')

        return v.lower()

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError('Invalid phone number')

        v = v.strip()
        phone_regex = re.compile(Regex.PHONE_REGEX)
        if not phone_regex.match(v):
            raise ValueError('Invalid phone number format')

        return v


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not isinstance(v, str):
            raise ValueError('Password must be a string')

        v = v.strip()
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')

        return v


class UserResponse(UserBase):
    id: int
    role: int | None = None
    created_at: datetime
    updated_at: datetime

    # ORM mode
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(UserBase):
    password: str | None = None
    email: str | None = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError('Password must be a string')

        v = v.strip()
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')

        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError('Invalid email address')

        v = v.strip()
        email_regex = re.compile(Regex.EMAIL_REGEX)
        if not email_regex.match(v):
            raise ValueError('Invalid email address')

        return v.lower()


class UserUpgradeRole(BaseModel):
    role: int

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in (0, 1, 2):
            raise ValueError('Invalid role value')
        return v


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


def update_user_by_id(
    db: DBSession, id: int, user_update: UserUpdate
) -> User | None:
    db_user = get_user_by_id(db, id)
    if not db_user:
        return None
    data = user_update.model_dump(exclude_unset=True)
    blocked_fields = {
        'id',
        'created_at',
        'updated_at',
    }
    for f in blocked_fields:
        data.pop(f, None)

    for field in list(data.keys()):
        if not hasattr(db_user, field):
            data.pop(field)
    for field, value in data.items():
        setattr(db_user, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Ví dụ: trùng unique gmail/phone → raise HTTP 409 ở layer API
        raise
    db.refresh(db_user)
    return db_user


def delete_user_by_id(db: DBSession, id: int) -> bool:
    db_user = get_user_by_id(db, id)
    if not db_user:
        return False
    db.delete(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    return True


def upgrade_user_role_by_id(
    db: DBSession, id: int, new_role: int
) -> User | None:
    new_author = None
    db_user = get_user_by_id(db, id)
    if not db_user:
        return None
    db_user.role = new_role

    if new_role == 1:
        exists = db.query(Author).filter(Author.user_id == db_user.id).first()
        if exists:
            raise ValueError('User is already an author')
        new_author = Author(pen_name=f'Author_{db_user.id}', user_id=db_user.id)
        db.add(new_author)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_user)
    if new_author is not None:
        db.refresh(new_author)
    return db_user


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


@router.patch(
    '/{id}', response_model=UserResponse, status_code=200, tags=['Users']
)
def update_user(id: int, user_update: UserUpdate, db: DBSession):
    db_user = update_user_by_id(db, id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')
    return db_user


@router.delete('/{id}', status_code=204, tags=['Users'])
def delete_user(id: int, db: DBSession):
    if not delete_user_by_id(db, id):
        raise HTTPException(status_code=404, detail='User not found')
    return None


@router.patch(
    '/{user_id}/role',
    response_model=UserResponse,
    status_code=200,
    tags=['Users'],
)
def upgrade_user_role(
    user_id: int, user_upgrade: UserUpgradeRole, db: DBSession
):
    try:
        db_user = upgrade_user_role_by_id(db, user_id, user_upgrade.role)
    except ValueError as e:
        # e.g., user is already an author -> conflict
        raise HTTPException(status_code=409, detail=str(e)) from None

    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')
    return db_user
