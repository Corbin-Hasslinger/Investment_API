from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, delete

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.core.config import Settings, get_settings
from atlas_api.main import create_app
from atlas_api.models.portfolios import Portfolio
from atlas_api.models.positions import Position
from atlas_api.models.securities import Security
from atlas_api.models.users import User
from atlas_api.repositories.security_repository import SecurityRepository
from atlas_api.services.security_service import SecurityService


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test")


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def engine(settings: Settings):
    engine = create_engine(settings.effective_database_url)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine) -> Iterator[Session]:
    with Session(engine) as session:
        session.exec(delete(Position))
        session.exec(delete(Security))
        session.exec(delete(Portfolio))
        session.exec(delete(User))
        session.commit()
        yield session


@pytest.fixture
def user(session) -> User:
    user = User(email=f"user-{uuid4()}@example.com", hashed_password="hashed")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def portfolio(session, user) -> Portfolio:
    portfolio = Portfolio(
        user_id=user.id, name="Demo Portfolio", description="Test portfolio"
    )
    session.add(portfolio)
    session.commit()
    session.refresh(portfolio)
    return portfolio


@pytest.fixture
def security(session) -> Security:
    security = Security(
        symbol="AAPL", name="Apple Inc", exchange="NASDAQ", currency="USD"
    )
    session.add(security)
    session.commit()
    session.refresh(security)
    return security


@pytest.fixture
def override_dependency(
    app: FastAPI,
) -> Iterator[Callable[[Callable[..., Any], Callable[..., Any]], None]]:
    def register(dependency: Callable[..., Any], override: Callable[..., Any]) -> None:
        app.dependency_overrides[dependency] = override

    yield register
    app.dependency_overrides.clear()


@pytest.fixture
def security_repository() -> MagicMock:
    """Create a mocked SecurityRepository for unit tests."""
    return MagicMock(spec=SecurityRepository)


@pytest.fixture
def finnhub_client() -> MagicMock:
    """Create a mocked FinnhubClient for unit tests."""
    return MagicMock(spec=FinnhubClient)


@pytest.fixture
def security_service(
    security_repository: MagicMock,
    finnhub_client: MagicMock,
) -> SecurityService:
    """Create a SecurityService with mocked dependencies for unit tests."""
    return SecurityService(
        security_repository=security_repository,
        finnhub_client=finnhub_client,
    )
