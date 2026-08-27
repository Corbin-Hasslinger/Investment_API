from decimal import Decimal
from typing import Any

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.schemas.stock import StockQuote
from atlas_api.services.security_service import SecurityService


class MarketDataService:
    """
    Owns market-data retrieval workflows.

    Responsibilities:
    - Fetch live quotes for tickers
    - Normalize symbols before querying
    - Transform Finnhub response into clean schema
    - Handle upstream errors at domain boundary
    """

    def __init__(
        self, finnhub_client: FinnhubClient, security_service: SecurityService
    ):
        self.finnhub_client = finnhub_client
        self.security_service = security_service

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        return Decimal(str(value))

    @staticmethod
    def _to_timestamp(value: Any) -> int:
        return int(value)

    async def get_quote(self, symbol: str) -> StockQuote:
        """
        Fetch a live market quote for a ticker symbol.

        Query operation: no database mutation.

        Process:
        1. Normalize ticker symbol
        2. Fetch quote from Finnhub
        3. Transform response to clean schema

        Returns:
            StockQuote: cleaned quote data with symbol, price, change, etc.

        Raises:
            InvalidSymbolFormatError: symbol format is invalid
            UpstreamTimeoutError: Finnhub request timed out
            UpstreamRateLimitedError: Finnhub rate limit exceeded
            UpstreamUnavailableError: Finnhub service unavailable
        """
        normalized_symbol = self.security_service.normalize_symbol(symbol)

        quote_data = await self.finnhub_client.get_quote(normalized_symbol)
        return StockQuote(
            symbol=normalized_symbol,
            current_price=self._to_decimal(quote_data["c"]),
            price_change=self._to_decimal(quote_data["d"]),
            percent_change=self._to_decimal(quote_data["dp"]),
            high_price=self._to_decimal(quote_data["h"]),
            low_price=self._to_decimal(quote_data["l"]),
            open_price=self._to_decimal(quote_data["o"]),
            previous_close_price=self._to_decimal(quote_data["pc"]),
            timestamp=self._to_timestamp(quote_data["t"]),
        )

    async def get_basic_financials(self, symbol: str) -> dict[str, Any]:
        """
        Fetch basic financials for a ticker symbol.

        Query operation: no database mutation.

        Process:
        1. Normalize ticker symbol
        2. Fetch basic financials from Finnhub

        Returns:
            dict[str, Any]: cleaned basic financials data

        Raises:
            InvalidSymbolFormatError: symbol format is invalid
            UpstreamTimeoutError: Finnhub request timed out
            UpstreamRateLimitedError: Finnhub rate limit exceeded
            UpstreamUnavailableError: Finnhub service unavailable
        """
        normalized_symbol = self.security_service.normalize_symbol(symbol)
        return await self.finnhub_client.get_basic_financials(normalized_symbol)
