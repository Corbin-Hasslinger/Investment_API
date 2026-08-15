from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from atlas_api.models.portfolios import Portfolio
from atlas_api.models.positions import Position
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.repositories.position_repository import PositionRepository
from atlas_api.repositories.security_repository import SecurityRepository
from atlas_api.schemas.position import PositionCreate, PositionRead, PositionUpdate
from atlas_api.services.position_service import PositionService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    PositionAlreadyExistsError,
    PositionNotFoundError,
    SecurityNotFoundError,
)
from atlas_api.tools.pagination import PaginationParams


def build_position(
    *,
    position_id: UUID | None = None,
    portfolio_id: UUID | None = None,
    security_id: UUID | None = None,
    shares: Decimal | str = "10.50",
    average_cost: Decimal | str = "102.00",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Position:
    timestamp = datetime.now(UTC)
    return Position(
        id=position_id or uuid4(),
        portfolio_id=portfolio_id or uuid4(),
        security_id=security_id or uuid4(),
        shares=Decimal(str(shares)),
        average_cost=Decimal(str(average_cost)),
        created_at=created_at or timestamp,
        updated_at=updated_at or timestamp,
    )


@pytest.fixture
def repository() -> MagicMock:
    mock = MagicMock(spec=PositionRepository)
    mock.exists_by_portfolio_and_security.return_value = False
    return mock


@pytest.fixture
def security_repository() -> MagicMock:
    return MagicMock(spec=SecurityRepository)


@pytest.fixture
def portfolio_repository() -> MagicMock:
    return MagicMock(spec=PortfolioRepository)


@pytest.fixture
def service(
    repository: MagicMock,
    security_repository: MagicMock,
    portfolio_repository: MagicMock,
) -> PositionService:
    return PositionService(
        position_repository=repository,
        security_repository=security_repository,
        portfolio_repository=portfolio_repository,
    )


def test_create_position_returns_position_read_for_valid_payload(
    service: PositionService,
    repository: MagicMock,
    security_repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    security_id = uuid4()
    security_repository.get_security_by_id.return_value = object()
    stored = build_position(
        position_id=uuid4(),
        portfolio_id=portfolio_id,
        security_id=security_id,
        shares="25.50",
        average_cost="110.00",
    )
    repository.create_position.return_value = stored

    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )

    result = service.create_position(
        PositionCreate(security_id=security_id, shares=Decimal("25.50"), average_cost=Decimal("110.00")),
        portfolio_id,
        user_id,
    )

    assert isinstance(result, PositionRead)
    assert result.id == stored.id
    assert result.security_id == security_id
    assert result.shares == Decimal("25.50")
    assert result.average_cost == Decimal("110.00")
    security_repository.get_security_by_id.assert_called_once_with(security_id)
    repository.exists_by_portfolio_and_security.assert_called_once_with(security_id, portfolio_id)
    created_model = repository.create_position.call_args.args[0]
    assert created_model.portfolio_id == portfolio_id
    assert created_model.security_id == security_id
    assert created_model.shares == Decimal("25.50")
    assert created_model.average_cost == Decimal("110.00")
    repository.commit.assert_called_once()
    repository.refresh.assert_called_once_with(stored)


def test_create_position_rejects_missing_security(
    service: PositionService,
    repository: MagicMock,
    security_repository: MagicMock,
    portfolio_repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    security_id = uuid4()
    user_id = uuid4()
    security_repository.get_security_by_id.return_value = None
    portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )

    with pytest.raises(SecurityNotFoundError):
        service.create_position(
            PositionCreate(security_id=security_id, shares=Decimal("5"), average_cost=Decimal("100")),
            portfolio_id,
            user_id,
        )

    repository.create_position.assert_not_called()
    repository.commit.assert_not_called()


def test_create_position_rejects_portfolio_not_owned_by_user(
    service: PositionService,
    repository: MagicMock,
    security_repository: MagicMock,
    portfolio_repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    security_id = uuid4()
    user_id = uuid4()
    security_repository.get_security_by_id.return_value = object()
    portfolio_repository.get_portfolio_by_id.return_value = None

    with pytest.raises(PortfolioNotFoundError):
        service.create_position(
            PositionCreate(security_id=security_id, shares=Decimal("5"), average_cost=Decimal("100")),
            portfolio_id,
            user_id,
        )

    repository.create_position.assert_not_called()
    repository.commit.assert_not_called()


def test_create_position_rejects_duplicate_portfolio_security_pair(
    service: PositionService,
    repository: MagicMock,
    security_repository: MagicMock,
    portfolio_repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    security_id = uuid4()
    user_id = uuid4()
    security_repository.get_security_by_id.return_value = object()
    portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )
    repository.exists_by_portfolio_and_security.return_value = True

    with pytest.raises(PositionAlreadyExistsError):
        service.create_position(
            PositionCreate(security_id=security_id, shares=Decimal("4"), average_cost=Decimal("90")),
            portfolio_id,
            user_id,
        )

    repository.create_position.assert_not_called()
    repository.commit.assert_not_called()


def test_get_all_positions_maps_repository_models_to_read_schemas(
    service: PositionService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)
    repository.get_all_positions.return_value = [
        build_position(
            position_id=uuid4(),
            portfolio_id=portfolio_id,
            security_id=uuid4(),
            shares="8.00",
            average_cost="55.00",
            created_at=older,
            updated_at=older,
        ),
        build_position(
            position_id=uuid4(),
            portfolio_id=portfolio_id,
            security_id=uuid4(),
            shares="12.50",
            average_cost="75.00",
            created_at=newer,
            updated_at=newer,
        ),
    ]

    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )

    result = service.get_all_positions(portfolio_id, user_id, PaginationParams(page=1, page_size=25))

    assert [type(item) for item in result.items] == [PositionRead, PositionRead]
    assert result.total == 2
    assert result.page == 1
    assert result.page_size == 25
    assert [item.shares for item in result.items] == [Decimal("8.00"), Decimal("12.50")]


def test_get_position_raises_not_found_when_repository_returns_none(
    service: PositionService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )
    repository.get_position_by_id.return_value = None

    with pytest.raises(PositionNotFoundError):
        service.get_position(uuid4(), portfolio_id, user_id)


def test_update_position_updates_only_provided_fields(
    service: PositionService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    existing = build_position(
        position_id=position_id,
        portfolio_id=portfolio_id,
        security_id=uuid4(),
        shares="10.00",
        average_cost="100.00",
    )
    updated = build_position(
        position_id=position_id,
        portfolio_id=portfolio_id,
        security_id=existing.security_id,
        shares="15.50",
        average_cost="100.00",
        created_at=existing.created_at,
        updated_at=existing.updated_at + timedelta(minutes=1),
    )
    repository.get_position_by_id.return_value = existing
    repository.update_position.return_value = updated

    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )

    result = service.update_position(
        position_id,
        portfolio_id,
        user_id,
        PositionUpdate(shares=Decimal("15.50")),
    )

    payload = repository.update_position.call_args.args[2]
    assert payload.model_dump(exclude_unset=True) == {"shares": Decimal("15.50")}
    assert result.shares == Decimal("15.50")
    assert result.average_cost == Decimal("100.00")
    repository.commit.assert_called_once()
    repository.refresh.assert_called_once_with(updated)


def test_delete_position_returns_true_when_position_exists(
    service: PositionService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    repository.get_position_by_id.return_value = build_position(
        position_id=position_id,
        portfolio_id=portfolio_id,
        security_id=uuid4(),
    )

    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )

    assert service.delete_position(position_id, portfolio_id, user_id) is True
    repository.delete_position.assert_called_once_with(position_id, portfolio_id)
    repository.commit.assert_called_once()


def test_delete_position_raises_not_found_when_position_missing(
    service: PositionService,
    repository: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    service.portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Test Portfolio",
    )
    repository.get_position_by_id.return_value = None

    with pytest.raises(PositionNotFoundError):
        service.delete_position(uuid4(), portfolio_id, user_id)

    repository.delete_position.assert_not_called()
