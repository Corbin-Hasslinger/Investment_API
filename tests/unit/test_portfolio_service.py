from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from atlas_api.models.portfolios import Portfolio
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.tools.errors import (
    InvalidPortfolioDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
)
from atlas_api.tools.pagination import PaginationParams


def build_portfolio(
    *,
    portfolio_id: UUID | None = None,
    user_id: UUID | None = None,
    name: str = "Core Holdings",
    description: str | None = "Long-term positions",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Portfolio:
    timestamp = datetime.now(UTC)
    return Portfolio(
        id=portfolio_id or uuid4(),
        user_id=user_id or uuid4(),
        name=name,
        description=description,
        created_at=created_at or timestamp,
        updated_at=updated_at or timestamp,
    )


@pytest.fixture
def repository() -> MagicMock:
    mock = MagicMock(spec=PortfolioRepository)
    mock.exists_by_name.return_value = False
    return mock


@pytest.fixture
def service(repository: MagicMock) -> PortfolioService:
    return PortfolioService(repository)


def test_create_portfolio_returns_portfolio_read_for_valid_create(
    service: PortfolioService, repository: MagicMock
) -> None:
    user_id = uuid4()
    stored = build_portfolio(user_id=user_id, name="Growth", description="Aggressive")
    repository.get_all_portfolios.return_value = []
    repository.create_portfolio.return_value = stored

    result = service.create_portfolio(
        PortfolioCreate(name=" Growth ", description="Aggressive"),
        user_id,
    )

    assert isinstance(result, PortfolioRead)
    assert result.id == stored.id
    assert result.user_id == user_id
    assert result.name == "Growth"
    assert result.description == "Aggressive"
    created_model = repository.create_portfolio.call_args.args[0]
    assert created_model.name == "Growth"
    assert created_model.description == "Aggressive"
    assert created_model.user_id == user_id


@pytest.mark.parametrize("name", ["   ", "\t\n  "])
def test_create_portfolio_rejects_blank_or_whitespace_names(
    service: PortfolioService,
    repository: MagicMock,
    name: str,
) -> None:
    repository.get_all_portfolios.return_value = []

    with pytest.raises(InvalidPortfolioDataError):
        service.create_portfolio(PortfolioCreate(name=name, description=None), uuid4())

    repository.create_portfolio.assert_not_called()


def test_create_portfolio_rejects_duplicate_normalized_names_for_same_user(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    user_id = uuid4()
    repository.exists_by_name.return_value = True

    with pytest.raises(PortfolioAlreadyExistsError):
        service.create_portfolio(
            PortfolioCreate(name="  retirement  ", description=None), user_id
        )

    repository.create_portfolio.assert_not_called()


def test_get_portfolio_raises_not_found_when_repository_returns_none(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    repository.get_portfolio_by_id.return_value = None

    with pytest.raises(PortfolioNotFoundError):
        service.get_portfolio(portfolio_id, user_id)


def test_get_all_portfolios_maps_repository_models_to_read_schemas(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    user_id = uuid4()
    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)
    repository.get_all_portfolios.return_value = [
        build_portfolio(
            user_id=user_id, name="Newer", created_at=newer, updated_at=newer
        ),
        build_portfolio(
            user_id=user_id, name="Older", created_at=older, updated_at=older
        ),
    ]

    result = service.get_all_portfolios(user_id, PaginationParams(page=1, page_size=25))

    assert [type(item) for item in result.items] == [PortfolioRead, PortfolioRead]
    assert [item.name for item in result.items] == ["Newer", "Older"]
    assert all(item.user_id == user_id for item in result.items)
    assert result.total == 2


def test_update_portfolio_updates_only_provided_fields(
    service: PortfolioService, repository: MagicMock
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    existing = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
        name="Core",
        description="Original description",
    )
    updated = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
        name="Core",
        description="Updated description",
        created_at=existing.created_at,
        updated_at=existing.updated_at + timedelta(minutes=1),
    )
    repository.get_portfolio_by_id.side_effect = [existing, updated]
    repository.get_all_portfolios.return_value = [existing]

    result = service.update_portfolio(
        portfolio_id,
        PortfolioUpdate(description="Updated description"),
        user_id,
    )

    update_payload = repository.update_portfolio.call_args.args[1]
    assert update_payload.model_dump(exclude_unset=True) == {
        "description": "Updated description"
    }
    assert result.description == "Updated description"
    assert result.name == "Core"


def test_update_portfolio_allows_description_none_to_clear_description(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    existing = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
        description="Needs clearing",
    )
    updated = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
        description=None,
        created_at=existing.created_at,
        updated_at=existing.updated_at + timedelta(minutes=1),
    )
    repository.get_portfolio_by_id.side_effect = [existing, updated]

    result = service.update_portfolio(
        portfolio_id, PortfolioUpdate(description=None), user_id
    )

    update_payload = repository.update_portfolio.call_args.args[1]
    assert update_payload.model_dump(exclude_unset=True) == {"description": None}
    assert result.description is None


def test_update_portfolio_rejects_name_none(
    service: PortfolioService, repository: MagicMock
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    repository.get_portfolio_by_id.return_value = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
    )

    with pytest.raises(InvalidPortfolioDataError):
        service.update_portfolio(portfolio_id, PortfolioUpdate(name=None), user_id)

    repository.update_portfolio.assert_not_called()


@pytest.mark.parametrize("name", ["   ", "\n\t "])
def test_update_portfolio_rejects_blank_or_whitespace_names(
    service: PortfolioService,
    repository: MagicMock,
    name: str,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    repository.get_portfolio_by_id.return_value = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
    )

    with pytest.raises(InvalidPortfolioDataError):
        service.update_portfolio(portfolio_id, PortfolioUpdate(name=name), user_id)

    repository.update_portfolio.assert_not_called()


def test_update_portfolio_rejects_duplicate_normalized_names_for_same_user(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    current = build_portfolio(portfolio_id=portfolio_id, user_id=user_id, name="Core")
    repository.get_portfolio_by_id.return_value = current
    repository.exists_by_name.return_value = True

    with pytest.raises(PortfolioAlreadyExistsError):
        service.update_portfolio(
            portfolio_id, PortfolioUpdate(name=" retirement "), user_id
        )

    repository.update_portfolio.assert_not_called()


def test_delete_portfolio_returns_true_when_row_exists(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    repository.get_portfolio_by_id.return_value = build_portfolio(
        portfolio_id=portfolio_id,
        user_id=user_id,
    )

    result = service.delete_portfolio(portfolio_id, user_id)

    assert result is True
    repository.delete_portfolio.assert_called_once_with(portfolio_id, user_id)


def test_delete_portfolio_raises_not_found_when_repository_returns_none(
    service: PortfolioService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    repository.get_portfolio_by_id.return_value = None

    with pytest.raises(PortfolioNotFoundError):
        service.delete_portfolio(portfolio_id, user_id)

    repository.delete_portfolio.assert_not_called()
