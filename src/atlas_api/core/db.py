from collections.abc import Generator
from functools import lru_cache

from sqlmodel import Session, create_engine

from atlas_api.core.config import get_settings


@lru_cache
def get_engine():
    """Returns a cached SQLAlchemy engine instance."""
    settings = get_settings()

    return create_engine(
        settings.effective_database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
    )


def get_session() -> Generator[Session]:
    """Returns a SQLAlchemy session."""
    session = Session(get_engine())
    try:
        yield session
    finally:
        session.close()
