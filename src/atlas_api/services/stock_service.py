

import httpx

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.schemas.stock import StockQuote


class StockService:
    def __init__(self, finnhub_client: FinnhubClient):
        self.finnhub_client = finnhub_client

    async def fetch_stock_quote(self, ticker: str) -> StockQuote:
        """Fetches the latest stock quote for the given ticker symbol, using the Finnhub API.
        
            Return fields: 
                c: Current price
                d: Price change
                dp: Percent change
                h: High price of the day
                l: Low price of the day
                o: Open price of the day
                pc: Previous close price
                t: Unix timestamp for the quote.
            """
        quote_data = await self.finnhub_client.get_quote(ticker)
        
        return StockQuote(
            ticker=ticker.upper(),
            current_price=quote_data["c"],
            price_change=quote_data["d"],
            percent_change=quote_data["dp"],
            high_price=quote_data["h"],
            low_price=quote_data["l"],
            open_price=quote_data["o"],
            previous_close_price=quote_data["pc"],
            timestamp=quote_data["t"]
        )