from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: int = 0
    type: str = 'user'


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[int] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)
