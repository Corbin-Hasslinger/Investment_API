from datetime import date

import httpx

from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

type JsonPrimitive = str | int | float | bool | None
type JsonValue = (
    JsonPrimitive
    | list[JsonValue]
    | dict[str, JsonValue]
)
type JsonObject = dict[str, JsonValue]


class FinnhubClient:
    BASE_URL = "https://finnhub.io/api/v1"
    REQUEST_TIMEOUT = 10.0

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @staticmethod
    def _expect_object(
        data: JsonValue,
        operation: str,
    ) -> JsonObject:
        if not isinstance(data, dict):
            raise UpstreamUnavailableError(
                f"Finnhub returned an invalid {operation} response."
            )
        return data

    @staticmethod
    def _expect_object_list(
        data: JsonValue,
        operation: str,
    ) -> list[dict[str, JsonValue]]:
        if not isinstance(data, list):
            raise UpstreamUnavailableError(
                f"Finnhub returned an invalid {operation} response."
            )

        objects: list[dict[str, JsonValue]] = []
        for item in data:
            if not isinstance(item, dict):
                raise UpstreamUnavailableError(
                    f"Finnhub returned an invalid {operation} response."
                )
            objects.append(item)
        return objects
    
    async def _get_json(
        self,
        path: str,
        params: dict[str, str | int | float | bool | None],
    ) -> JsonValue:
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

    async def get_quote(self, symbol: str) -> dict[str, JsonValue]:
        """Fetches the latest stock quote for the given ticker symbol from Finnhub API."""
        data = await self._get_json(
            "quote", 
            {
                "symbol": symbol
            }
        )
        return self._expect_object(data, "Quote")

    async def get_company_profile(self, symbol: str) -> dict[str, JsonValue]:
        """Return company profile data for the given ticker symbol."""
        data = await self._get_json(
            "stock/profile2", 
            {
                "symbol": symbol
            }
        )
        return self._expect_object(data, "Company Profile")

    async def get_basic_financials(self, symbol: str) -> dict[str, JsonValue]:
        """Return basic financials for the given ticker symbol."""
        data = await self._get_json(
                "stock/metric",
                {
                    "symbol": symbol,
                    "metric": "all",
                },
            )
        return self._expect_object(data, "Basic Financials")
    
    async def get_company_news(self, 
                               symbol: str, 
                               from_date: date,
                               to_date: date
                               ) -> list[dict[str, JsonValue]]:
        """Return the latest company news for the given ticker symbol."""
        data = await self._get_json(
            "company-news",
            {
                "symbol": symbol,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            },
        )

        return self._expect_object_list(data, "Company News")