from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


users_follow_authors = Table(
    'users_follow_authors',
    Base.metadata,
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'author_id',
        Integer,
        ForeignKey('authors.id', ondelete='CASCADE'),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(100), index=True, unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Many-to-Many relationship: links User to Authors they follow
    following = relationship(
        'Author', secondary=users_follow_authors, back_populates='followers'
    )


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, index=True)
    pen_name = Column(String(128), unique=True, index=True)

    # Foreign key to the User who is the Author
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )

    # One-to-One relationship back to the User object
    profile = relationship('User', backref='author', uselist=False)

    # Many-to-Many relationship: links Author to Users who follow them
    followers = relationship(
        'User', secondary=users_follow_authors, back_populates='following'
    )
