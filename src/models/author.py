from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from .user import User

from .associations import user_author_follows
from ..database import Base


class Author(Base):
    __tablename__ = 'authors'

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True,
    )

    pen_name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    biography: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    followers: Mapped[list[User]] = relationship(
        'User',
        secondary=user_author_follows,
        back_populates='follow_authors',
        primaryjoin=lambda: Author.user_id == user_author_follows.c.author_id,
        secondaryjoin=lambda: User.user_id == user_author_follows.c.user_id,
        lazy='selectin',
        cascade='save-update',
    )

    __mapper__args__ = {
        'polymorphic_identity': 'author',
    }
