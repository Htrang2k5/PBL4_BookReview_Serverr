from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from src.models import reaction
    from .postReport import PostReport
    from .postView import PostView
    from .comment import Comment
from ..database import Base


class Post(Base):
    __tablename__ = 'posts'
    post_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    cover: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # anh bia sach
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(MEDIUMTEXT, nullable=False)
    credit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    author_id: Mapped[int] = mapped_column(
        ForeignKey('authors.user_id'), nullable=True
    )
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    status: Mapped[str] = mapped_column(String(50), default='waiting')
    cout_likes: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    count_reports: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    count_comments: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    count_views: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    count_dislikes: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    link_sale: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    post: Mapped[list[PostView]] = relationship(
        'PostView', back_populates='post', cascade='all, delete-orphan'
    )

    comments: Mapped[list[Comment]] = relationship(
        'Comment', back_populates='post', cascade='all, delete-orphan'
    )
    reactions: Mapped[list['reaction.Reacton']] = relationship(
        'Reacton', back_populates='post', cascade='all, delete-orphan'
    )

    post_reports: Mapped[list[PostReport]] = relationship(
        'PostReport',
        back_populates='post',
        cascade='all, delete-orphan',
    )
