from typing import Any

import httpx

from atlas_api.tools.errors import UpstreamRateLimitedError, UpstreamTimeoutError, UpstreamUnavailableError


class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def get_quote(self, ticker: str) -> dict[str, Any]:
        """Fetches the latest stock quote for the given ticker symbol from Finnhub API."""
        url = f"{self.BASE_URL}/quote"
        params = {
            "symbol": ticker.upper(),
        }
        headers = {
            "X-Finnhub-Token": self.api_key
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError(
                "Finnhub request timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise UpstreamRateLimitedError(
                    "Finnhub rate limit exceeded."
                ) from exc
            if 500 <= exc.response.status_code < 600:
                raise UpstreamUnavailableError(
                    "Finnhub service unavailable."
                ) from exc
            raise
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError(
                "Unable to communicate with Finnhub."
            ) from exc

        return response.json()

    async def is_valid_symbol(self, symbol: str) -> dict[str, Any]:
        """ Checks if the given ticker symbol is valid by querying Finnhub's profile2 endpoint."""
        url = f"{self.BASE_URL}/stock/profile2"
        params = {
            "symbol": symbol,
        }
        headers = {
            "X-Finnhub-Token": self.api_key,
        }
        try: 
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers )
            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError(
            "Finnhub request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise UpstreamRateLimitedError(
                    "Finnhub rate limit exceeded."
                ) from exc

            if 500 <= exc.response.status_code < 600:
                raise UpstreamUnavailableError(
                "Finnhub service unavailable."
            ) from exc

            raise

        except httpx.RequestError as exc:
            raise UpstreamUnavailableError(
            "Unable to communicate with Finnhub."
        ) from exc

        return response.json()  # Returns the symbol data if it exists, indicating a valid symbol