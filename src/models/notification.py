from __future__ import annotations
from sqlalchemy import ForeignKey, Integer, DateTime, String, Index
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .notificationRecipient import NotificationRecipient
    from .user import User


class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    # Use the actual users PK column name 'user_id'
    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True
    )
    post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=True
    )
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Liên kết đối tượng (tối giản)
    related_object_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_object_id: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    # The notification recipients are stored in the association table
    # `notification_recipients`. Keep sender relationship but remove
    # a direct `user` relationship and any indexes that referenced
    # columns not present on this table (e.g. user_id, is_read).
    sender: Mapped[Optional['User']] = relationship(
        'User', foreign_keys=[sender_id], lazy='selectin'
    )

    __table_args__ = (Index('ix_notifications_created_at', 'created_at'),)

    recipients: Mapped[list[NotificationRecipient]] = relationship(
        'NotificationRecipient',
        back_populates='notification',
        cascade='all, delete-orphan',
        passive_deletes=True,
        lazy='selectin',  # mặc định: load gộp hiệu quả
    )
