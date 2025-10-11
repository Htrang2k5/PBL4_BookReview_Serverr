from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from ..database import Base


from .notification import Notification
from .user import User


class NotificationRecipient(Base):
    __tablename__ = 'notification_recipients'

    notification_id: Mapped[int] = mapped_column(
        ForeignKey('notifications.id', ondelete='CASCADE'), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True
    )

    # Trạng thái tối giản
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Thời gian tạo/cập nhật record trung gian
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Quan hệ ngược
    notification: Mapped['Notification'] = relationship(
        'Notification', back_populates='recipients', lazy='selectin'
    )
    user: Mapped['User'] = relationship(
        'User', back_populates='notification_items', lazy='selectin'
    )

    # Index tối ưu hóa truy vấn hộp thư user
    __table_args__ = (
        Index(
            'ix_notirec_user_isread_created', 'user_id', 'is_read', 'created_at'
        ),
    )
