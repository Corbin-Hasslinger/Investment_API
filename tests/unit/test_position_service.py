from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from atlas_api.models.portfolios import Portfolio
from atlas_api.models.positions import Position
from atlas_api.schemas.position import PositionCreate, PositionRead, PositionUpdate
from atlas_api.schemas.security import SecurityRead
from atlas_api.services.position_service import PositionService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    PositionAlreadyExistsError,
    PositionNotFoundError,
)
from atlas_api.tools.pagination import PaginationParams


def build_position(
    *,
    position_id=None,
    portfolio_id=None,
    symbol="AAPL",
    shares="10.50",
    average_cost="102.00",
    created_at=None,
    updated_at=None,
) -> Position:
    timestamp = datetime.now(UTC)
    return Position(
        id=position_id or uuid4(),
        portfolio_id=portfolio_id or uuid4(),
        symbol=symbol,
        shares=Decimal(str(shares)),
        average_cost=Decimal(str(average_cost)),
        created_at=created_at or timestamp,
        updated_at=updated_at or timestamp,
    )


@pytest.fixture
def repository() -> MagicMock:
    mock = MagicMock()
    mock.exists_by_portfolio_and_security.return_value = False
    return mock


@pytest.fixture
def portfolio_repository() -> MagicMock:
    return MagicMock()


@pytest.fixture
def security_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(repository, portfolio_repository, security_service) -> PositionService:
    return PositionService(
        position_repository=repository,
        portfolio_repository=portfolio_repository,
        security_service=security_service,
    )


@pytest.fixture
def portfolio_and_user(portfolio_repository):
    portfolio_id = uuid4()
    user_id = uuid4()
    portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
        description=None,
    )
    return portfolio_id, user_id


def security_read(symbol="AAPL") -> SecurityRead:
    timestamp = datetime.now(UTC)
    return SecurityRead(
        id=uuid4(),
        symbol=symbol,
        name="Apple Inc",
        exchange="NASDAQ",
        currency="USD",
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_create_position_resolves_symbol_and_persists_position(
    service, repository, security_service, portfolio_and_user
) -> None:
    portfolio_id, user_id = portfolio_and_user
    resolved = security_read("AAPL")
    security_service.resolve_security = AsyncMock(return_value=resolved)
    stored = build_position(
        position_id=uuid4(),
        portfolio_id=portfolio_id,
        symbol="AAPL",
        shares="25.50",
        average_cost="110.00",
    )
    repository.create_position.return_value = stored

    result = await service.create_position(
        PositionCreate(
            symbol=" aapl ", shares=Decimal("25.50"), average_cost=Decimal("110.00")
        ),
        portfolio_id,
        user_id,
    )

    assert isinstance(result, PositionRead)
    assert result.symbol == "AAPL"
    security_service.resolve_security.assert_awaited_once_with(" aapl ")
    repository.exists_by_portfolio_and_security.assert_called_once_with(
        "AAPL", portfolio_id
    )
    created = repository.create_position.call_args.args[0]
    assert created.symbol == "AAPL"
    repository.commit.assert_called_once()
    repository.refresh.assert_called_once_with(stored)


@pytest.mark.asyncio
async def test_create_position_rejects_duplicate(
    service, repository, security_service, portfolio_and_user
) -> None:
    portfolio_id, user_id = portfolio_and_user
    security_service.resolve_security = AsyncMock(return_value=security_read("AAPL"))
    repository.exists_by_portfolio_and_security.return_value = True

    with pytest.raises(PositionAlreadyExistsError):
        await service.create_position(
            PositionCreate(symbol="AAPL", shares=Decimal(4), average_cost=Decimal(90)),
            portfolio_id,
            user_id,
        )

    repository.create_position.assert_not_called()
    repository.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_position_rejects_unowned_portfolio(
    service, repository, security_service, portfolio_repository
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    portfolio_repository.get_portfolio_by_id.return_value = None

    with pytest.raises(PortfolioNotFoundError):
        await service.create_position(
            PositionCreate(symbol="AAPL", shares=Decimal(5), average_cost=Decimal(100)),
            portfolio_id,
            user_id,
        )

    security_service.resolve_security.assert_not_called()
    repository.create_position.assert_not_called()


def test_get_all_positions_maps_models_to_read_schemas(
    service, repository, portfolio_repository
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)
    repository.get_all_positions.return_value = [
        build_position(
            portfolio_id=portfolio_id, symbol="AAPL", created_at=older, updated_at=older
        ),
        build_position(
            portfolio_id=portfolio_id, symbol="MSFT", created_at=newer, updated_at=newer
        ),
    ]
    portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id, user_id=user_id, name="Test Portfolio", description=None
    )

    result = service.get_all_positions(
        portfolio_id, user_id, PaginationParams(page=1, page_size=25)
    )

    assert [type(item) for item in result.items] == [PositionRead, PositionRead]
    assert [item.symbol for item in result.items] == ["AAPL", "MSFT"]


def test_get_position_raises_when_missing(
    service, repository, portfolio_and_user
) -> None:
    portfolio_id, user_id = portfolio_and_user
    repository.get_position_by_id.return_value = None

    with pytest.raises(PositionNotFoundError):
        service.get_position(uuid4(), portfolio_id, user_id)


def test_update_position_updates_provided_fields(
    service, repository, portfolio_and_user
) -> None:
    portfolio_id, user_id = portfolio_and_user
    position_id = uuid4()
    existing = build_position(position_id=position_id, portfolio_id=portfolio_id)
    updated = build_position(
        position_id=position_id, portfolio_id=portfolio_id, shares="15.50"
    )
    repository.get_position_by_id.return_value = existing
    repository.update_position.return_value = updated

    result = service.update_position(
        position_id, portfolio_id, user_id, PositionUpdate(shares=Decimal("15.50"))
    )

    assert result.shares == Decimal("15.50")
    repository.commit.assert_called_once()
    repository.refresh.assert_called_once_with(updated)


def test_delete_position_returns_true(service, repository, portfolio_and_user) -> None:
    portfolio_id, user_id = portfolio_and_user
    position_id = uuid4()
    repository.get_position_by_id.return_value = build_position(
        position_id=position_id, portfolio_id=portfolio_id
    )

    assert service.delete_position(position_id, portfolio_id, user_id) is True
    repository.delete_position.assert_called_once_with(position_id, portfolio_id)
    repository.commit.assert_called_once()
