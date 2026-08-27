from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from atlas_api.schemas.analytics import (
    PortfolioAnalyticsRead,
    PortfolioPositionAnalyticsRead,
)


def build_position_read() -> PortfolioPositionAnalyticsRead:
    return PortfolioPositionAnalyticsRead(
        symbol="AAPL",
        shares=Decimal("10"),
        average_cost=Decimal("100.00"),
        current_price=Decimal("125.00"),
        market_value=Decimal("1250.00"),
        cost_basis=Decimal("1000.00"),
        unrealized_gain_loss=Decimal("250.00"),
        unrealized_gain_loss_percent=Decimal("25.00"),
        allocation_percent=Decimal("100.00"),
    )


class TestPortfolioPositionAnalyticsReadSerialization:
    """Test suite for PortfolioPositionAnalyticsRead JSON serialization."""

    def test_model_dump_json_serializes_decimals_as_strings(self):
        position = build_position_read()

        dumped = position.model_dump(mode="json")

        assert dumped == {
            "symbol": "AAPL",
            "shares": "10",
            "average_cost": "100.00",
            "current_price": "125.00",
            "market_value": "1250.00",
            "cost_basis": "1000.00",
            "unrealized_gain_loss": "250.00",
            "unrealized_gain_loss_percent": "25.00",
            "allocation_percent": "100.00",
        }

    def test_model_dump_python_mode_keeps_decimal_types(self):
        position = build_position_read()

        dumped = position.model_dump()

        assert isinstance(dumped["shares"], Decimal)
        assert isinstance(dumped["market_value"], Decimal)
        assert isinstance(dumped["unrealized_gain_loss_percent"], Decimal)

    def test_unrealized_gain_loss_percent_none_serializes_as_null(self):
        position = build_position_read().model_copy(
            update={"unrealized_gain_loss_percent": None}
        )

        dumped = position.model_dump(mode="json")

        assert dumped["unrealized_gain_loss_percent"] is None


class TestPortfolioAnalyticsReadSerialization:
    """Test suite for PortfolioAnalyticsRead JSON serialization."""

    def test_model_dump_json_serializes_expected_shape(self):
        portfolio_id = uuid4()
        analytics = PortfolioAnalyticsRead(
            portfolio_id=portfolio_id,
            total_market_value=Decimal("1250.00"),
            total_cost_basis=Decimal("1000.00"),
            total_unrealized_gain_loss=Decimal("250.00"),
            total_unrealized_gain_loss_percent=Decimal("25.00"),
            positions=[build_position_read()],
        )

        dumped = analytics.model_dump(mode="json")

        assert dumped == {
            "portfolio_id": str(portfolio_id),
            "total_market_value": "1250.00",
            "total_cost_basis": "1000.00",
            "total_unrealized_gain_loss": "250.00",
            "total_unrealized_gain_loss_percent": "25.00",
            "positions": [
                {
                    "symbol": "AAPL",
                    "shares": "10",
                    "average_cost": "100.00",
                    "current_price": "125.00",
                    "market_value": "1250.00",
                    "cost_basis": "1000.00",
                    "unrealized_gain_loss": "250.00",
                    "unrealized_gain_loss_percent": "25.00",
                    "allocation_percent": "100.00",
                }
            ],
        }

    def test_model_dump_json_serializes_empty_positions_list(self):
        portfolio_id = uuid4()
        analytics = PortfolioAnalyticsRead(
            portfolio_id=portfolio_id,
            total_market_value=Decimal("0.00"),
            total_cost_basis=Decimal("0.00"),
            total_unrealized_gain_loss=Decimal("0.00"),
            total_unrealized_gain_loss_percent=None,
            positions=[],
        )

        dumped = analytics.model_dump(mode="json")

        assert dumped["positions"] == []
        assert dumped["total_unrealized_gain_loss_percent"] is None

    def test_extra_fields_are_forbidden(self):
        payload = {
            "portfolio_id": str(uuid4()),
            "total_market_value": "0.00",
            "total_cost_basis": "0.00",
            "total_unrealized_gain_loss": "0.00",
            "positions": [],
            "unexpected_field": "not allowed",
        }
        with pytest.raises(ValidationError):
            PortfolioAnalyticsRead.model_validate(payload)

    def test_position_extra_fields_are_forbidden(self):
        payload = {
            "symbol": "AAPL",
            "shares": "10",
            "average_cost": "100.00",
            "current_price": "125.00",
            "market_value": "1250.00",
            "cost_basis": "1000.00",
            "unrealized_gain_loss": "250.00",
            "unrealized_gain_loss_percent": "25.00",
            "allocation_percent": "100.00",
            "unexpected_field": "not allowed",
        }

        with pytest.raises(ValidationError):
            PortfolioPositionAnalyticsRead.model_validate(payload)
