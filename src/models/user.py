from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .postView import PostView
    from .author import Author
    from .notification import NotificationRecipient
    from .comment import Comment
    from .reaction import Reaction
    from .postReport import PostReport

from .associations import user_author_follows


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(100), index=True, unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    role: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # discriminator cho kế thừa đa hình
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default='user'
    )
    follow_authors: Mapped[list[Author]] = relationship(
        'Author',
        secondary=user_author_follows,
        back_populates='followers',
        lazy='selectin',
        cascade='save-update',
        primaryjoin=lambda: User.user_id == user_author_follows.c.user_id,
        secondaryjoin=lambda: Author.user_id == user_author_follows.c.author_id,
    )
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user',
    }

    post_views: Mapped[list[PostView]] = relationship(
        'PostView', back_populates='user', cascade='all, delete-orphan'
    )

    comments: Mapped[list[Comment]] = relationship(
        'Comment', back_populates='user', cascade='all, delete-orphan'
    )
    reactions: Mapped[list[Reaction]] = relationship(
        'Reacton', back_populates='user', cascade='all, delete-orphan'
    )
    notification_items: Mapped[list[NotificationRecipient]] = relationship(
        'NotificationRecipient',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy='selectin',
    )
    post_reports: Mapped[list[PostReport]] = relationship(
        'PostReport',
        back_populates='user',
        cascade='all, delete-orphan',
    )
