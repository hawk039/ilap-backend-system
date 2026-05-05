from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(
        settings.resolved_sync_database_url,
        future=True,
        pool_pre_ping=True,
    )


@lru_cache
def get_session_local():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


engine = get_engine()
SessionLocal = get_session_local()


def get_db() -> Generator[Session, None, None]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
