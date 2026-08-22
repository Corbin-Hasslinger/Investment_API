from unittest.mock import AsyncMock, MagicMock

from atlas_api.di import get_market_data_service
from atlas_api.schemas.stock import StockQuote
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.tools.errors import InvalidSymbolFormatError, UpstreamTimeoutError


def test_get_quote_returns_200_with_valid_data(client, override_dependency):
    """GET /market/quote/{ticker} returns 200 with quote data."""
    market_data_service = MagicMock(spec=MarketDataService)
    market_data_service.get_quote = AsyncMock(return_value=StockQuote(
        symbol="AAPL",
        current_price=150.25,
        price_change=2.50,
        percent_change=1.69,
        high_price=152.00,
        low_price=149.50,
        open_price=149.00,
        previous_close_price=147.75,
        timestamp=1692374400,
    ))

    override_dependency(get_market_data_service, lambda: market_data_service)

    response = client.get("/market/quote/AAPL")

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    assert response.json()["current_price"] == "150.25"


def test_get_quote_returns_400_for_invalid_symbol(client, override_dependency):
    """GET /market/quote/{ticker} returns 400 for invalid symbol."""
    market_data_service = MagicMock(spec=MarketDataService)
    market_data_service.get_quote = AsyncMock(
        side_effect=InvalidSymbolFormatError("Invalid format")
    )

    override_dependency(get_market_data_service, lambda: market_data_service)

    response = client.get("/market/quote/TOOLONG6CHARS")

    assert response.status_code == 400


def test_get_quote_returns_503_for_upstream_timeout(client, override_dependency):
    """GET /market/quote/{ticker} returns 503 for upstream timeout."""
    market_data_service = MagicMock(spec=MarketDataService)
    market_data_service.get_quote = AsyncMock(
        side_effect=UpstreamTimeoutError("Timeout")
    )

    override_dependency(get_market_data_service, lambda: market_data_service)

    response = client.get("/market/quote/AAPL")

    assert response.status_code == 504

