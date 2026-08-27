import httpx

from atlas_api.tools import (
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class TickerbotClient:
    REQUEST_TIMEOUT = 10.0

    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _expect_object(data: JsonValue, operation: str) -> JsonObject:
        if not isinstance(data, dict):
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid {operation} response."
            )
        return data

    @staticmethod
    def _validate_scan_response(data: JsonObject) -> JsonObject:
        results = data.get("results")

        if not isinstance(results, list):
            raise UpstreamResponseError(
                "Expected 'results' to be a list in scan response."
            )
        for result in results:
            if not isinstance(result, dict):
                raise UpstreamResponseError(
                    "Expected each item in 'results' to be an object in scan response."
                )
        return data

    async def scan(
        self,
        query: str,
        order: str,
        direction: str,
        limit: int,
        columns: list[str],
        cursor: str | None = None,
    ) -> JsonObject:
        url = f"{self.base_url}/scan"
        json_columns: list[JsonValue] = list(columns)
        asset_class: list[JsonValue] = ["stocks"]
        payload: dict[str, JsonValue] = {
            "q": query,
            "order": order,
            "dir": direction,
            "limit": limit,
            "columns": json_columns,
            "asset_class": asset_class,
        }
        if cursor is not None:
            payload["cursor"] = cursor

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    url=url,
                    json=payload,
                    headers=headers,
                )
            response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Tickerbot request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise UpstreamRateLimitedError(
                    "Tickerbot rate limit exceeded."
                ) from exc
            if exc.response.status_code == 400:
                raise UpstreamResponseError(
                    "Tickerbot rejected the screening request."
                ) from exc
            if exc.response.status_code == 401:
                raise UpstreamUnavailableError(
                    "Tickerbot authentication failed."
                ) from exc
            if exc.response.status_code == 402:
                raise UpstreamUnavailableError(
                    "Tickerbot request quota exceeded."
                ) from exc
            if exc.response.status_code == 403:
                raise UpstreamUnavailableError(
                    "Tickerbot rejected the requested capability."
                ) from exc
            if 500 <= exc.response.status_code < 600:
                raise UpstreamUnavailableError(
                    "Tickerbot service unavailable."
                ) from exc
            raise UpstreamResponseError(
                "Tickerbot returned an unexpected error response."
            ) from exc
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError(
                "Unable to communicate with Tickerbot."
            ) from exc
        try:
            data: JsonValue = response.json()
        except ValueError as exc:
            raise UpstreamResponseError("Failed to parse Tickerbot response.") from exc

        return self._validate_scan_response(
            self._expect_object(data, "stock screening")
        )
