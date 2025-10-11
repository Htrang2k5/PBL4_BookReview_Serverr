from typing import Optional
from sqlalchemy import (
    String,
    ForeignKey,
    Integer,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

from .post import Post
from .user import User


class PostReport(Base):
    __tablename__ = 'post_reports'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    user: Mapped[User] = relationship('User', back_populates='post_reports')
    post: Mapped[Post] = relationship('Post', back_populates='post_reports')

    __table_args__ = (
        UniqueConstraint(
            'user_id', 'post_id', name='uq_post_reports_user_post'
        ),
        Index('ix_post_reports_post_id', 'post_id'),
        Index('ix_post_reports_user_id', 'user_id'),
        Index('ix_post_reports_created_at', 'created_at'),
    )
