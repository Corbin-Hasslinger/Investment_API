from decimal import Decimal
from uuid import uuid4

from atlas_api.schemas.analytics import PortfolioPositionAnalyticsRead
from atlas_api.services.analysis_calculations import AnalysisCalculations


def build_position(
    *,
    symbol: str,
    shares: Decimal,
    average_cost: Decimal,
    current_price: Decimal,
    market_value: Decimal,
    cost_basis: Decimal,
    unrealized_gain_loss: Decimal,
    unrealized_gain_loss_percent: Decimal | None = None,
) -> PortfolioPositionAnalyticsRead:
    return PortfolioPositionAnalyticsRead(
        symbol=symbol,
        shares=shares,
        average_cost=average_cost,
        current_price=current_price,
        market_value=market_value,
        cost_basis=cost_basis,
        unrealized_gain_loss=unrealized_gain_loss,
        unrealized_gain_loss_percent=unrealized_gain_loss_percent,
        allocation_percent=Decimal("0.00"),
    )

class TestCalculatePositionAnalytics:
    """Test suite for AnalysisCalculations.calculate_position_analytics()."""

    def test_single_winning_position(self):
        calculations = AnalysisCalculations()

        result = calculations.calculate_position_analytics(
            symbol="AAPL",
            shares=Decimal("10"),
            average_cost=Decimal("100.00"),
            current_price=Decimal("125.00"),
        )

        assert result.cost_basis == Decimal("1000.00")
        assert result.market_value == Decimal("1250.00")
        assert result.unrealized_gain_loss == Decimal("250.00")
        assert result.unrealized_gain_loss_percent == Decimal("25.00")
        assert result.allocation_percent == Decimal("0.00")

    def test_losing_position(self):
        calculations = AnalysisCalculations()

        result = calculations.calculate_position_analytics(
            symbol="AAPL",
            shares=Decimal("10"),
            average_cost=Decimal("125.00"),
            current_price=Decimal("100.00"),
        )

        assert result.cost_basis == Decimal("1250.00")
        assert result.market_value == Decimal("1000.00")
        assert result.unrealized_gain_loss == Decimal("-250.00")
        assert result.unrealized_gain_loss_percent == Decimal("-20.00")
        assert result.allocation_percent == Decimal("0.00")

    def test_zero_cost_basis_returns_none_percent_without_raising(self):
        calculations = AnalysisCalculations()

        result = calculations.calculate_position_analytics(
            symbol="FREE",
            shares=Decimal("10"),
            average_cost=Decimal("0.00"),
            current_price=Decimal("50.00"),
        )

        assert result.cost_basis == Decimal("0.00")
        assert result.market_value == Decimal("500.00")
        assert result.unrealized_gain_loss == Decimal("500.00")
        assert result.unrealized_gain_loss_percent is None

    def test_fractional_shares(self):
        calculations = AnalysisCalculations()

        result = calculations.calculate_position_analytics(
            symbol="AAPL",
            shares=Decimal("2.5"),
            average_cost=Decimal("100.00"),
            current_price=Decimal("120.00"),
        )

        assert result.cost_basis == Decimal("250.00")
        assert result.market_value == Decimal("300.00")
        assert result.unrealized_gain_loss == Decimal("50.00")
        assert result.unrealized_gain_loss_percent == Decimal("20.00")
        assert result.allocation_percent == Decimal("0.00")

    def test_decimal_precision_avoids_float_rounding_errors(self):
        calculations = AnalysisCalculations()

        result = calculations.calculate_position_analytics(
            symbol="AAPL",
            shares=Decimal("3.333"),
            average_cost=Decimal("10.01"),
            current_price=Decimal("10.02"),
        )

        assert result.cost_basis == Decimal("33.36")
        assert result.market_value == Decimal("33.40")
        assert result.unrealized_gain_loss == Decimal("0.03")
        assert result.unrealized_gain_loss_percent == Decimal("0.09")
        assert isinstance(result.cost_basis, Decimal)
        assert isinstance(result.market_value, Decimal)
        assert isinstance(result.unrealized_gain_loss, Decimal)
        assert isinstance(result.unrealized_gain_loss_percent, Decimal)


class TestCalculatePortfolioAnalytics:
    """Test suite for AnalysisCalculations.calculate_portfolio_analytics()."""

    def test_multiple_positions_allocation_percent(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()
        positions = [
            build_position(
                symbol="AAPL",
                shares=Decimal("10"),
                average_cost=Decimal("75.00"),
                current_price=Decimal("75.00"),
                market_value=Decimal("750.00"),
                cost_basis=Decimal("750.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
            build_position(
                symbol="MSFT",
                shares=Decimal("5"),
                average_cost=Decimal("50.00"),
                current_price=Decimal("50.00"),
                market_value=Decimal("250.00"),
                cost_basis=Decimal("250.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(portfolio_id, positions)

        by_symbol = {position.symbol: position for position in result.positions}
        assert by_symbol["AAPL"].allocation_percent == Decimal("75.00")
        assert by_symbol["MSFT"].allocation_percent == Decimal("25.00")
        assert result.total_market_value == Decimal("1000.00")

    def test_empty_portfolio(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()

        result = calculations.calculate_portfolio_analytics(portfolio_id, [])

        assert result.portfolio_id == portfolio_id
        assert result.positions == []
        assert result.total_market_value == Decimal("0.00")
        assert result.total_cost_basis == Decimal("0.00")
        assert result.total_unrealized_gain_loss == Decimal("0.00")
        assert result.total_unrealized_gain_loss_percent is None

    def test_zero_total_cost_basis_returns_none_percent_without_raising(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()
        positions = [
            build_position(
                symbol="FREE",
                shares=Decimal("10"),
                average_cost=Decimal("0.00"),
                current_price=Decimal("50.00"),
                market_value=Decimal("500.00"),
                cost_basis=Decimal("0.00"),
                unrealized_gain_loss=Decimal("500.00"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(portfolio_id, positions)

        assert result.total_cost_basis == Decimal("0.00")
        assert result.total_unrealized_gain_loss_percent is None

    def test_allocation_percents_total_100(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()
        positions = [
            build_position(
                symbol="AAPL",
                shares=Decimal("3"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("100.00"),
                market_value=Decimal("300.00"),
                cost_basis=Decimal("300.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
            build_position(
                symbol="MSFT",
                shares=Decimal("3"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("100.00"),
                market_value=Decimal("300.00"),
                cost_basis=Decimal("300.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
            build_position(
                symbol="GOOG",
                shares=Decimal("4"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("100.00"),
                market_value=Decimal("400.00"),
                cost_basis=Decimal("400.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(portfolio_id, positions)

        total_allocation = sum(
            (position.allocation_percent for position in result.positions),
            Decimal("0.00"),
        )
        assert total_allocation == Decimal("100.00")

    def test_positions_are_ordered_by_symbol(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()
        positions = [
            build_position(
                symbol="MSFT",
                shares=Decimal("1"),
                average_cost=Decimal("10.00"),
                current_price=Decimal("10.00"),
                market_value=Decimal("10.00"),
                cost_basis=Decimal("10.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
            build_position(
                symbol="AAPL",
                shares=Decimal("1"),
                average_cost=Decimal("10.00"),
                current_price=Decimal("10.00"),
                market_value=Decimal("10.00"),
                cost_basis=Decimal("10.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
            build_position(
                symbol="GOOG",
                shares=Decimal("1"),
                average_cost=Decimal("10.00"),
                current_price=Decimal("10.00"),
                market_value=Decimal("10.00"),
                cost_basis=Decimal("10.00"),
                unrealized_gain_loss=Decimal("0.00"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(portfolio_id, positions)

        assert [position.symbol for position in result.positions] == ["AAPL", "GOOG", "MSFT"]

    def test_portfolio_gain_loss_percent_uses_total_values(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()

        positions = [
            build_position(
                symbol="AAPL",
                shares=Decimal("10"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("110.00"),
                market_value=Decimal("1100.00"),
                cost_basis=Decimal("1000.00"),
                unrealized_gain_loss=Decimal("100.00"),
                unrealized_gain_loss_percent=Decimal("10.00"),
            ),
            build_position(
                symbol="MSFT",
                shares=Decimal("1"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("150.00"),
                market_value=Decimal("150.00"),
                cost_basis=Decimal("100.00"),
                unrealized_gain_loss=Decimal("50.00"),
                unrealized_gain_loss_percent=Decimal("50.00"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(
            portfolio_id,
            positions,
        )

        assert result.total_cost_basis == Decimal("1100.00")
        assert result.total_market_value == Decimal("1250.00")
        assert result.total_unrealized_gain_loss == Decimal("150.00")
        assert result.total_unrealized_gain_loss_percent == Decimal("13.64")

    def test_allocation_rounding_policy(self):
        calculations = AnalysisCalculations()
        portfolio_id = uuid4()

        positions = [
            build_position(
                symbol="AAA",
                shares=Decimal("1"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("33.33"),
                market_value=Decimal("33.33"),
                cost_basis=Decimal("100.00"),
                unrealized_gain_loss=Decimal("-66.67"),
            ),
            build_position(
                symbol="BBB",
                shares=Decimal("1"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("33.33"),
                market_value=Decimal("33.33"),
                cost_basis=Decimal("100.00"),
                unrealized_gain_loss=Decimal("-66.67"),
            ),
            build_position(
                symbol="CCC",
                shares=Decimal("1"),
                average_cost=Decimal("100.00"),
                current_price=Decimal("33.34"),
                market_value=Decimal("33.34"),
                cost_basis=Decimal("100.00"),
                unrealized_gain_loss=Decimal("-66.66"),
            ),
        ]

        result = calculations.calculate_portfolio_analytics(
            portfolio_id,
            positions,
        )

        allocations = {
            position.symbol: position.allocation_percent
            for position in result.positions
        }

        assert allocations == {
            "AAA": Decimal("33.33"),
            "BBB": Decimal("33.33"),
            "CCC": Decimal("33.34"),
        }