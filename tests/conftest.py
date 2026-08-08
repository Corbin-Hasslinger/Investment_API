from collections.abc import Callable, Iterator
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, delete

from atlas_api.core.config import Settings, get_settings
from atlas_api.main import create_app
from atlas_api.models.portfolios import Portfolio
from atlas_api.models.users import User


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
def override_dependency(app: FastAPI) -> Iterator[Callable[[Callable[..., Any], Callable[..., Any]], None]]:
    def register(dependency: Callable[..., Any], override: Callable[..., Any]) -> None:
        app.dependency_overrides[dependency] = override

    yield register
    app.dependency_overrides.clear()

