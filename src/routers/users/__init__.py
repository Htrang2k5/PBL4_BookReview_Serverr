from fastapi import APIRouter, HTTPException

from src.database import DBSession
from src.models.user import User

from . import schema

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', response_model=schema.User)
async def create_user(user: schema.UserCreate, db: DBSession):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get('/', response_model=list[schema.User])
async def read_users(db: DBSession, page: int = 1, page_size: int = 10):
    users = (
        db.query(User)
        .order_by(User.email.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return users


@router.get('/{user_id}', response_model=schema.User)
async def read_user(user_id: int, db: DBSession):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')

    return user
