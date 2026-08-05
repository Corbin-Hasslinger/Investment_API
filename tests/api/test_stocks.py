from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_api.core.config import Settings
from atlas_api.di import get_finnhub_client, get_stock_service
from atlas_api.services.stock_service import StockService


def test_get_finnhub_client_requires_api_key() -> None:
    settings = Settings(environment="test", finnhub_api_key=None)

    with pytest.raises(ValueError, match="FINNHUB_API_KEY"):
        get_finnhub_client(settings)


def test_get_stock_quote_uses_dependency_override(client, override_dependency) -> None:
    stock_service = MagicMock(spec=StockService)
    stock_service.fetch_stock_quote = AsyncMock(
        return_value={
            "ticker": "AAPL",
            "current_price": 210.5,
            "price_change": 1.2,
            "percent_change": 0.57,
            "high_price": 211.0,
            "low_price": 208.2,
            "open_price": 209.1,
            "previous_close_price": 209.3,
            "timestamp": 1722787200,
        }
    )

    override_dependency(get_stock_service, lambda: stock_service)

    response = client.get("/stocks/AAPL/quote")

    assert response.status_code == 200
    assert response.json() == {
        "ticker": "AAPL",
        "current_price": 210.5,
        "price_change": 1.2,
        "percent_change": 0.57,
        "high_price": 211.0,
        "low_price": 208.2,
        "open_price": 209.1,
        "previous_close_price": 209.3,
        "timestamp": 1722787200,
    }
    stock_service.fetch_stock_quote.assert_awaited_once_with("AAPL")