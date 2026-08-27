from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call
from uuid import UUID, uuid4

import pytest

from atlas_api.models.portfolios import Portfolio
from atlas_api.models.positions import Position
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.repositories.position_repository import PositionRepository
from atlas_api.schemas.analytics import (
    PortfolioAnalyticsRead,
    PortfolioPositionAnalyticsRead,
)
from atlas_api.schemas.stock import StockQuote
from atlas_api.services.analysis_calculations import AnalysisCalculations
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.tools.errors import PortfolioNotFoundError, UpstreamTimeoutError


def build_position(
    *,
    portfolio_id: UUID,
    symbol: str,
    shares: Decimal = Decimal("10"),
    average_cost: Decimal = Decimal("100.00"),
) -> Position:
    return Position(
        id=uuid4(),
        portfolio_id=portfolio_id,
        symbol=symbol,
        shares=shares,
        average_cost=average_cost,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def build_quote(symbol: str, current_price: Decimal) -> StockQuote:
    return StockQuote(
        symbol=symbol,
        current_price=current_price,
        price_change=Decimal("0.00"),
        percent_change=Decimal("0.00"),
        high_price=current_price,
        low_price=current_price,
        open_price=current_price,
        previous_close_price=current_price,
        timestamp=1_692_374_400,
    )


def build_position_analytics(symbol: str) -> PortfolioPositionAnalyticsRead:
    return PortfolioPositionAnalyticsRead(
        symbol=symbol,
        shares=Decimal("10"),
        average_cost=Decimal("100.00"),
        current_price=Decimal("125.00"),
        market_value=Decimal("1250.00"),
        cost_basis=Decimal("1000.00"),
        unrealized_gain_loss=Decimal("250.00"),
        unrealized_gain_loss_percent=Decimal("25.00"),
        allocation_percent=Decimal("100.00"),
    )


def build_portfolio_analytics(
    portfolio_id: UUID,
    positions: list[PortfolioPositionAnalyticsRead],
) -> PortfolioAnalyticsRead:
    return PortfolioAnalyticsRead(
        portfolio_id=portfolio_id,
        total_market_value=sum(
            (position.market_value for position in positions), Decimal("0.00")
        ),
        total_cost_basis=sum(
            (position.cost_basis for position in positions), Decimal("0.00")
        ),
        total_unrealized_gain_loss=sum(
            (position.unrealized_gain_loss for position in positions), Decimal("0.00")
        ),
        total_unrealized_gain_loss_percent=None,
        positions=positions,
    )


@pytest.fixture
def portfolio_repository() -> MagicMock:
    return MagicMock(spec=PortfolioRepository)


@pytest.fixture
def position_repository() -> MagicMock:
    return MagicMock(spec=PositionRepository)


@pytest.fixture
def market_data_service() -> MagicMock:
    service = MagicMock(spec=MarketDataService)
    service.get_quote = AsyncMock()
    return service


@pytest.fixture
def analysis_calculations() -> MagicMock:
    return MagicMock(spec=AnalysisCalculations)


@pytest.fixture
def service(
    analysis_calculations: MagicMock,
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
) -> PortfolioAnalyticsService:
    return PortfolioAnalyticsService(
        analysis_calculations=analysis_calculations,
        portfolio_repository=portfolio_repository,
        position_repository=position_repository,
        market_data_service=market_data_service,
    )


@pytest.fixture
def portfolio_and_user(portfolio_repository: MagicMock) -> tuple[UUID, UUID]:
    portfolio_id = uuid4()
    user_id = uuid4()
    portfolio_repository.get_portfolio_by_id.return_value = Portfolio(
        id=portfolio_id,
        user_id=user_id,
        name="Analytics Portfolio",
        description=None,
    )
    return portfolio_id, user_id


def assert_read_only_repositories(
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
) -> None:
    for repository in (portfolio_repository, position_repository):
        for method_name in ("commit", "flush", "refresh"):
            method = getattr(repository, method_name, None)
            if method is not None:
                method.assert_not_called()

    for method_name in ("create_position", "update_position", "delete_position"):
        getattr(position_repository, method_name).assert_not_called()


@pytest.mark.asyncio
async def test_get_portfolio_analytics_calculates_single_position(
    service: PortfolioAnalyticsService,
    portfolio_and_user: tuple[UUID, UUID],
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
    analysis_calculations: MagicMock,
) -> None:
    portfolio_id, user_id = portfolio_and_user
    position = build_position(portfolio_id=portfolio_id, symbol="AAPL")
    calculated_position = build_position_analytics("AAPL")
    expected = build_portfolio_analytics(portfolio_id, [calculated_position])
    position_repository.get_all_positions.return_value = [position]
    market_data_service.get_quote.return_value = build_quote("AAPL", Decimal("125.00"))
    analysis_calculations.calculate_position_analytics.return_value = (
        calculated_position
    )
    analysis_calculations.calculate_portfolio_analytics.return_value = expected

    result = await service.get_portfolio_analytics(portfolio_id, user_id)

    assert result is expected
    portfolio_repository.get_portfolio_by_id.assert_called_once_with(
        portfolio_id, user_id
    )
    position_repository.get_all_positions.assert_called_once_with(portfolio_id)
    market_data_service.get_quote.assert_awaited_once_with("AAPL")
    analysis_calculations.calculate_position_analytics.assert_called_once_with(
        "AAPL",
        position.shares,
        position.average_cost,
        Decimal("125.00"),
    )
    analysis_calculations.calculate_portfolio_analytics.assert_called_once_with(
        portfolio_id,
        [calculated_position],
    )
    assert_read_only_repositories(portfolio_repository, position_repository)


@pytest.mark.asyncio
async def test_get_portfolio_analytics_calculates_all_positions(
    service: PortfolioAnalyticsService,
    portfolio_and_user: tuple[UUID, UUID],
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
    analysis_calculations: MagicMock,
) -> None:
    portfolio_id, user_id = portfolio_and_user
    aapl_position = build_position(portfolio_id=portfolio_id, symbol="AAPL")
    msft_position = build_position(portfolio_id=portfolio_id, symbol="MSFT")
    aapl_analytics = build_position_analytics("AAPL")
    msft_analytics = build_position_analytics("MSFT")
    calculated_positions = [aapl_analytics, msft_analytics]
    expected = build_portfolio_analytics(portfolio_id, calculated_positions)
    position_repository.get_all_positions.return_value = [aapl_position, msft_position]
    market_data_service.get_quote.side_effect = [
        build_quote("AAPL", Decimal("125.00")),
        build_quote("MSFT", Decimal("300.00")),
    ]
    analysis_calculations.calculate_position_analytics.side_effect = (
        calculated_positions
    )
    analysis_calculations.calculate_portfolio_analytics.return_value = expected

    result = await service.get_portfolio_analytics(portfolio_id, user_id)

    assert result is expected
    assert market_data_service.get_quote.await_args_list == [call("AAPL"), call("MSFT")]
    assert analysis_calculations.calculate_position_analytics.call_args_list == [
        call(
            "AAPL", aapl_position.shares, aapl_position.average_cost, Decimal("125.00")
        ),
        call(
            "MSFT", msft_position.shares, msft_position.average_cost, Decimal("300.00")
        ),
    ]
    analysis_calculations.calculate_portfolio_analytics.assert_called_once_with(
        portfolio_id,
        calculated_positions,
    )
    assert_read_only_repositories(portfolio_repository, position_repository)


@pytest.mark.asyncio
async def test_get_portfolio_analytics_returns_empty_portfolio_result(
    service: PortfolioAnalyticsService,
    portfolio_and_user: tuple[UUID, UUID],
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
    analysis_calculations: MagicMock,
) -> None:
    portfolio_id, user_id = portfolio_and_user
    expected = build_portfolio_analytics(portfolio_id, [])
    position_repository.get_all_positions.return_value = []
    analysis_calculations.calculate_portfolio_analytics.return_value = expected

    result = await service.get_portfolio_analytics(portfolio_id, user_id)

    assert result is expected
    position_repository.get_all_positions.assert_called_once_with(portfolio_id)
    market_data_service.get_quote.assert_not_called()
    analysis_calculations.calculate_position_analytics.assert_not_called()
    analysis_calculations.calculate_portfolio_analytics.assert_called_once_with(
        portfolio_id, []
    )
    assert result.positions == []
    assert result.total_market_value == Decimal("0.00")
    assert result.total_cost_basis == Decimal("0.00")
    assert result.total_unrealized_gain_loss == Decimal("0.00")
    assert_read_only_repositories(portfolio_repository, position_repository)


@pytest.mark.asyncio
async def test_get_portfolio_analytics_raises_when_portfolio_is_not_owned(
    service: PortfolioAnalyticsService,
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
    analysis_calculations: MagicMock,
) -> None:
    portfolio_id = uuid4()
    user_id = uuid4()
    portfolio_repository.get_portfolio_by_id.return_value = None

    with pytest.raises(PortfolioNotFoundError):
        await service.get_portfolio_analytics(portfolio_id, user_id)

    portfolio_repository.get_portfolio_by_id.assert_called_once_with(
        portfolio_id, user_id
    )
    position_repository.get_all_positions.assert_not_called()
    market_data_service.get_quote.assert_not_called()
    analysis_calculations.calculate_position_analytics.assert_not_called()
    analysis_calculations.calculate_portfolio_analytics.assert_not_called()
    assert_read_only_repositories(portfolio_repository, position_repository)


@pytest.mark.asyncio
async def test_get_portfolio_analytics_propagates_quote_failure_without_calculating_portfolio(
    service: PortfolioAnalyticsService,
    portfolio_and_user: tuple[UUID, UUID],
    portfolio_repository: MagicMock,
    position_repository: MagicMock,
    market_data_service: MagicMock,
    analysis_calculations: MagicMock,
) -> None:
    portfolio_id, user_id = portfolio_and_user
    position_repository.get_all_positions.return_value = [
        build_position(portfolio_id=portfolio_id, symbol="AAPL")
    ]
    market_data_service.get_quote.side_effect = UpstreamTimeoutError("Timed out")

    with pytest.raises(UpstreamTimeoutError):
        await service.get_portfolio_analytics(portfolio_id, user_id)

    market_data_service.get_quote.assert_awaited_once_with("AAPL")
    analysis_calculations.calculate_position_analytics.assert_not_called()
    analysis_calculations.calculate_portfolio_analytics.assert_not_called()
    assert_read_only_repositories(portfolio_repository, position_repository)
