from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from atlas_api.core.config import Settings
from atlas_api.main import create_app


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


@pytest.fixture
def override_dependency(app: FastAPI) -> Iterator[Callable[[Callable[..., Any], Callable[..., Any]], None]]:
    def register(dependency: Callable[..., Any], override: Callable[..., Any]) -> None:
        app.dependency_overrides[dependency] = override

    yield register
    app.dependency_overrides.clear()