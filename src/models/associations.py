from __future__ import annotations
from sqlalchemy import (
    Table,
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)

from ..database import Base

user_author_follows = Table(
    'user_author_follows',
    Base.metadata,
    Column(
        'user_id',
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'author_id',
        ForeignKey('authors.user_id', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'followed_at',
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    UniqueConstraint('user_id', 'author_id', name='uq_user_author_follow_once'),
)
