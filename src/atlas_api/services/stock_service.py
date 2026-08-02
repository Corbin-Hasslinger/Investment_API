import os

import httpx
from dotenv import load_dotenv

from atlas_api.schemas.stock import StockQuote

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

class StockService:

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
        if not FINNHUB_API_KEY:
            raise ValueError("Finnhub API key not found in environment variables.")
        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": ticker.upper(),
            "token": FINNHUB_API_KEY
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            quote_data = response.json()
            return StockQuote(
                ticker=ticker.upper(),
                current_price=quote_data.get("c"),
                price_change=quote_data.get("d"),
                percent_change=quote_data.get("dp"),
                high_price=quote_data.get("h"),
                low_price=quote_data.get("l"),
                open_price=quote_data.get("o"),
                previous_close_price=quote_data.get("pc"),
                timestamp=quote_data.get("t")
            )