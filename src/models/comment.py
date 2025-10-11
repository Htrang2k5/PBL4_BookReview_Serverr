from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    ForeignKey,
    Integer,
    DateTime,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class Comment(Base):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False
    )
    content: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )

    user: Mapped[User] = relationship('User', back_populates='comments')
    post: Mapped[Post] = relationship('Post', back_populates='comments')

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_comments_user_post'),
        Index('ix_comments_post_id', 'post_id'),
        Index('ix_comments_user_id', 'user_id'),
        Index('ix_comments_created_at', 'created_at'),
    )
