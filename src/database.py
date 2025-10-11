from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.constants import Settings

# Create the SQLAlchemy engine
# The 'connect_args' is needed only for SQLite to allow multi-threaded access.
engine = create_engine(
    Settings.SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)

# Create a SessionLocal class.
# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create a Base class for our ORM models to inherit from.
class Base(DeclarativeBase):
    pass


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create an annotated dependency.
# This creates a new "type" that FastAPI understands.
DBSession = Annotated[Session, Depends(get_db)]
