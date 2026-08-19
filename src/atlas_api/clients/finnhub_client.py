from typing import Any

import httpx

from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)


class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"
    REQUEST_TIMEOUT = 10.0

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def _get_json(
        self,
        path: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{self.BASE_URL}/{path}"
        headers = {"X-Finnhub-Token": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.REQUEST_TIMEOUT,
                )
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

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Fetches the latest stock quote for the given ticker symbol from Finnhub API."""
        return await self._get_json("quote", {"symbol": symbol.upper()})

    async def symbol_lookup(self, symbol: str) -> dict[str, Any]:
        """Return company profile data for the given ticker symbol."""
        return await self._get_json("stock/profile2", {"symbol": symbol})