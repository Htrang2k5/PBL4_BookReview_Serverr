from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.constants import Settings

# Create the SQLAlchemy engine
engine = create_engine(Settings.SQLALCHEMY_DATABASE_URL)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create an annotated dependency.
DBSession = Annotated[Session, Depends(get_db)]
