from __future__ import annotations
from typing import Optional
from sqlalchemy import ForeignKey, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .post import Post
from .user import User


class PostView(Base):
    __tablename__ = 'post_views'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False
    )
    first_view_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    last_view_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    count_views: Mapped[Optional[int]] = mapped_column(Integer, default=1)

    post: Mapped[Post] = relationship('Post', back_populates='post_views')
    user: Mapped[User] = relationship('User', back_populates='post_views')

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='uq_post_views_user_post'),
        Index('ix_post_views_post_id', 'post_id'),
        Index('ix_post_views_user_id', 'user_id'),
        Index('ix_post_views_last_viewed_at', 'last_view_at'),
    )
