import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    created_at = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


class UsersFollowAuthors(Base):
    __tablename__ = 'users_follow_authors'

    user_id = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    author_id = mapped_column(
        Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True
    )


class User(Base):
    __tablename__ = 'users'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    email = mapped_column(String(100), unique=True, nullable=False, index=True)
    password = mapped_column(String(128), nullable=False)
    phone_number = mapped_column(String(16), nullable=True)

    # Relationships
    following = relationship(
        'Author',
        secondary=UsersFollowAuthors,
        back_populates='followers',
        cascade='all, delete-orphan',
    )


class Author(Base):
    __tablename__ = 'authors'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    pen_name = mapped_column(String(128), unique=True, index=True)

    # Foreign keys
    user_id = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )

    # Relationships
    profile = relationship(
        'User', backref='author', uselist=False, cascade='all, delete-orphan'
    )
    followers = relationship(
        'User',
        secondary=UsersFollowAuthors,
        back_populates='following',
        cascade='all, delete-orphan',
    )


class RequestStatus(enum.Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class Post(Base):
    __tablename__ = 'posts'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    cover_url = mapped_column(String(256), nullable=True)
    title = mapped_column(String(256), nullable=False)
    content = mapped_column(Text(1024), nullable=False)
    credit = mapped_column(String(256), nullable=True)
    status = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False
    )
    sale_url = mapped_column(String(256), nullable=True)

    # Foreign keys
    author_id = mapped_column(
        Integer, ForeignKey('authors.id', ondelete='CASCADE'), nullable=True
    )

    # Relationships
    author = relationship(
        'Author', backref='posts', cascade='all, delete-orphan'
    )
    comments = relationship(
        'Comment', back_populates='post', cascade='all, delete-orphan'
    )
    reactions = relationship(
        'Reaction', back_populates='post', cascade='all, delete-orphan'
    )
    reports = relationship(
        'PostReport', back_populates='post', cascade='all, delete-orphan'
    )


class Comment(Base):
    __tablename__ = 'comments'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    content = mapped_column(Text(512), nullable=False)

    # Foreign keys
    user_id = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    post_id = mapped_column(
        Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False
    )

    # Relationships
    user = relationship(
        'User', backref='comments', cascade='all, delete-orphan'
    )
    post = relationship(
        'Post', back_populates='comments', cascade='all, delete-orphan'
    )


class ReactionType(enum.Enum):
    LIKE = 'LIKE'
    DISLIKE = 'DISLIKE'


class Reaction(Base):
    __tablename__ = 'reactions'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    type = mapped_column(Enum(ReactionType), nullable=False)

    # Foreign keys
    user_id = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    post_id = mapped_column(
        Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False
    )

    # Relationships
    user = relationship(
        'User', backref='reactions', cascade='all, delete-orphan'
    )
    post = relationship(
        'Post', back_populates='reactions', cascade='all, delete-orphan'
    )


class PostReport(Base):
    __tablename__ = 'post_reports'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    reason = mapped_column(Text(512), nullable=False)
    status = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False
    )

    # Foreign keys
    user_id = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    post_id = mapped_column(
        Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False
    )

    # Relationships
    user = relationship(
        'User', backref='post_reports', cascade='all, delete-orphan'
    )
    post = relationship(
        'Post', back_populates='reports', cascade='all, delete-orphan'
    )


class Notification(Base):
    __tablename__ = 'notifications'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    title = mapped_column(String(128), nullable=False)
    message = mapped_column(Text(512), nullable=False)

    # Foreign keys
    recipient_id = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationships
    recipient = relationship(
        'User', backref='notifications', cascade='all, delete-orphan'
    )


class NotificationRecipient(Base):
    __tablename__ = 'notification_recipients'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    notification_id = mapped_column(
        Integer,
        ForeignKey('notifications.id', ondelete='CASCADE'),
        nullable=False,
    )
    user_id = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    is_read = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    notification = relationship(
        'Notification', backref='recipients', cascade='all, delete-orphan'
    )
    user = relationship(
        'User', backref='notification_recipients', cascade='all, delete-orphan'
    )
