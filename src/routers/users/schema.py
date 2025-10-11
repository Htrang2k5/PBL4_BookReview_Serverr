import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    phone_number: str | None = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Pydantic V2 config for ORM mode
    model_config = ConfigDict(from_attributes=True)
