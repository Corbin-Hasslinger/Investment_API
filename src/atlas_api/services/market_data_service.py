

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
    def __init__(self, 
                 finnhub_client: FinnhubClient, 
                 security_service: SecurityService
                 ):
        self.finnhub_client = finnhub_client
        self.security_service = security_service

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
            current_price=quote_data["c"],
            price_change=quote_data["d"],
            percent_change=quote_data["dp"],
            high_price=quote_data["h"],
            low_price=quote_data["l"],
            open_price=quote_data["o"],
            previous_close_price=quote_data["pc"],
            timestamp=quote_data["t"]
        )