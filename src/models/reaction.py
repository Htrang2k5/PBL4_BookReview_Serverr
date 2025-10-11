from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Optional
from sqlalchemy import ForeignKey, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .post import Post


class Reaction(Base):
    __tablename__ = 'reactions'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    type: Mapped[Literal['like', 'dislike']] = mapped_column(
        Enum('like', 'dislike', name='reaction_enum'), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id'), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.post_id'), nullable=False
    )
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    user: Mapped[User] = relationship('User', back_populates='reactions')
    post: Mapped[Post] = relationship('Post', back_populates='reactions')
