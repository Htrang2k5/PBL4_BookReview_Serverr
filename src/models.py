import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    created_at = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


users_follow_authors = Table(
    'users_follow_authors',
    Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('author_id', ForeignKey('authors.id'), primary_key=True),
    UniqueConstraint('user_id', 'author_id'),
)


class User(Base):
    __tablename__ = 'users'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    email = mapped_column(String(100), unique=True, nullable=False, index=True)
    password = mapped_column(String(128), nullable=False)
    phone_number = mapped_column(String(16), nullable=True)
    role = mapped_column(Integer, default=0)

    # Relationships

    Author = relationship(
        'Author',
        back_populates='profile',
        cascade='all, delete-orphan',
        single_parent=True,
        uselist=False,
    )

    following = relationship(
        'Author',
        secondary=users_follow_authors,
        back_populates='followers',
    )

    comments = relationship(
        'Comment',
        back_populates='user',
        cascade='all, delete-orphan',
        single_parent=True,
    )
    reactions = relationship(
        'Reaction',
        back_populates='user',
        cascade='all, delete-orphan',
        single_parent=True,
    )
    post_reports = relationship(
        'PostReport',
        back_populates='user',
        cascade='all, delete-orphan',
        single_parent=True,
    )
    notifications = relationship(
        'Notification',
        back_populates='recipient',
        cascade='all, delete-orphan',
        single_parent=True,
    )

    notification_recipients = relationship(
        'NotificationRecipient',
        back_populates='user',
        cascade='all, delete-orphan',
        single_parent=True,
    )


class Author(Base):
    __tablename__ = 'authors'

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    pen_name = mapped_column(String(128), unique=True, index=True)
    bio = mapped_column(Text(255), nullable=True)

    # Foreign keys
    user_id = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )

    # Relationships
    profile = relationship(
        'User',
        back_populates='Author',
        single_parent=True,
    )
    followers = relationship(
        'User',
        secondary=users_follow_authors,
        back_populates='following',
    )
    posts = relationship(
        'Post',
        back_populates='author',
        cascade='all, delete-orphan',
        single_parent=True,
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
    content = mapped_column(Text(65000), nullable=False)
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
        'Author',
        back_populates='posts',
    )
    comments = relationship(
        'Comment',
        back_populates='post',
        cascade='all, delete-orphan',
        single_parent=True,
    )
    reactions = relationship(
        'Reaction',
        back_populates='post',
        cascade='all, delete-orphan',
        single_parent=True,
    )
    reports = relationship(
        'PostReport',
        back_populates='post',
        cascade='all, delete-orphan',
        single_parent=True,
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
    user = relationship('User', back_populates='comments')
    post = relationship('Post', back_populates='comments')


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
    user = relationship('User', back_populates='reactions')
    post = relationship('Post', back_populates='reactions')


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
    user = relationship('User', back_populates='post_reports')
    post = relationship('Post', back_populates='reports')


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
    recipient = relationship('User', back_populates='notifications')
    recipients = relationship(
        'NotificationRecipient',
        back_populates='notification',
        cascade='all, delete-orphan',
        single_parent=True,
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
    notification = relationship('Notification', back_populates='recipients')
    user = relationship('User', back_populates='notification_recipients')
