import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database import DBSession
from src.models import session

from . import users


# Schemas
class SessionCreate(BaseModel):
    user_id: int


# CRUD operations


def generate_token():
    token = secrets.token_hex(32)

    expires_at = datetime.now() + timedelta(days=7)
    return token, expires_at


def create_session(db: DBSession, payload: SessionCreate) -> session:
    token, expires_at = generate_token()
    new_session = session(
        user_id=payload.user_id, token=token, expires_at=expires_at
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def delete_session_by_token(db: DBSession, token: str) -> bool:
    db_session = db.query(session).filter(session.token == token).first()
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True


def update_session_expiry(db: DBSession, token: str) -> session | None:
    db_session = db.query(session).filter(session.token == token).first()
    if not db_session:
        return None
    new_expiry = datetime.now() + timedelta(days=7)
    db_session.expires_at = new_expiry
    db.commit()
    db.refresh(db_session)
    return db_session


## Routes

router = APIRouter(prefix='/sessions', tags=['Sessions'])


@router.post('/login')
async def login_user(db: DBSession, email: str, password: str):
    db_user = users.check_user_login(db, email, password)
    if not db_user:
        raise HTTPException(status_code=401, detail='Invalid user account')
    # create new session or token here (omitted for brevity)
    new_session = create_session(db, SessionCreate(user_id=db_user.id))
    return {
        'message': 'Login successful',
        'user_id': db_user.id,
        'session_token': new_session.token,
    }


@router.post('/logout')
async def logout_user(db: DBSession, token: str):
    success = delete_session_by_token(db, token)
    if not success:
        raise HTTPException(status_code=400, detail='Invalid session token')
    return {'message': 'Logout successful'}


@router.post('/refresh-token')
async def refresh_session_token(db: DBSession, token: str):
    updated_session = update_session_expiry(db, token)
    if not updated_session:
        raise HTTPException(
            status_code=400, detail='Invalid session token! Login again'
        )
    return {
        'message': 'Session token refreshed',
        'new_expiry': updated_session.expires_at,
    }
