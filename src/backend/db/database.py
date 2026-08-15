"""SQLAlchemy engine, session, and database initialization helpers."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mllsp.db")


def _resolve_database_url(database_url: str) -> str:
    """Resolve relative SQLite paths from the repository root."""

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    database_path = database_url[len(prefix) :]
    if database_path in {":memory:", ""}:
        return database_url

    path = Path(database_path)
    if path.is_absolute():
        return database_url

    repository_root = Path(__file__).resolve().parents[3]
    return f"{prefix}{(repository_root / path).as_posix()}"


DATABASE_URL = _resolve_database_url(DATABASE_URL)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all database models."""


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and close it after use."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables that do not already exist."""

    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)