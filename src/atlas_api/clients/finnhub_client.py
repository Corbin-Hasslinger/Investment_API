from typing import Any

import httpx


class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def get_quote(self, ticker: str) -> dict[str, Any]:
        """Fetches the latest stock quote for the given ticker symbol from Finnhub API."""
        url = f"{self.BASE_URL}/quote"
        params = {
            "symbol": ticker.upper(),
            "token": self.api_key
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

        response.raise_for_status()

        return response.json()