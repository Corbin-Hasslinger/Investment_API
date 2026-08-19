from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_api.schemas.stock import StockQuote
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.tools.errors import (
    InvalidSymbolFormatError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
)


@pytest.fixture
def market_data_service(security_service, finnhub_client):
    """Create a MarketDataService with mocked dependencies."""
    return MarketDataService(
        security_service=security_service,
        finnhub_client=finnhub_client,
    )


class TestGetQuote:
    """Test suite for MarketDataService.get_quote()"""

    @pytest.mark.asyncio
    async def test_get_quote_returns_transformed_response(
        self,
        market_data_service: MarketDataService,
        finnhub_client: MagicMock,
    ):
        """get_quote() returns StockQuote with clean field names."""
        finnhub_client.get_quote = AsyncMock(return_value={
            "c": 150.25,      # current price
            "d": 2.50,        # change
            "dp": 1.69,       # percent change
            "h": 152.00,      # high
            "l": 149.50,      # low
            "o": 149.00,      # open
            "pc": 147.75,     # previous close
            "t": 1692374400,  # timestamp
        })

        result = await market_data_service.get_quote("aapl")

        assert isinstance(result, StockQuote)
        assert result.symbol == "AAPL"
        assert result.current_price == 150.25
        assert result.price_change == 2.50
        assert result.percent_change == 1.69
        finnhub_client.get_quote.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_get_quote_normalizes_symbol(
        self,
        market_data_service: MarketDataService,
        finnhub_client: MagicMock,
    ):
        """get_quote() normalizes symbol before fetching."""
        finnhub_client.get_quote = AsyncMock(return_value={
            "c": 100.0, "d": 0, "dp": 0, "h": 100, "l": 100,
            "o": 100, "pc": 100, "t": 1692374400,
        })

        await market_data_service.get_quote(" msft ")

        # Verify normalized symbol was passed to Finnhub
        finnhub_client.get_quote.assert_called_once_with("MSFT")

    @pytest.mark.asyncio
    async def test_get_quote_raises_invalid_symbol_on_bad_format(
        self,
        market_data_service: MarketDataService,
    ):
        """get_quote() raises InvalidSymbolFormatError for bad format."""
        with pytest.raises(InvalidSymbolFormatError):
            await market_data_service.get_quote("TOOLONG6CHARS")

    @pytest.mark.asyncio
    async def test_get_quote_propagates_upstream_timeout(
        self,
        market_data_service: MarketDataService,
        finnhub_client: MagicMock,
    ):
        """get_quote() propagates UpstreamTimeoutError from Finnhub."""
        finnhub_client.get_quote = AsyncMock(
            side_effect=UpstreamTimeoutError("Timeout")
        )

        with pytest.raises(UpstreamTimeoutError):
            await market_data_service.get_quote("AAPL")

    @pytest.mark.asyncio
    async def test_get_quote_propagates_upstream_rate_limit(
        self,
        market_data_service: MarketDataService,
        finnhub_client: MagicMock,
    ):
        """get_quote() propagates UpstreamRateLimitedError from Finnhub."""
        finnhub_client.get_quote = AsyncMock(
            side_effect=UpstreamRateLimitedError("Rate limited")
        )

        with pytest.raises(UpstreamRateLimitedError):
            await market_data_service.get_quote("AAPL")