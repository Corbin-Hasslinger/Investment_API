from unittest.mock import AsyncMock

import httpx
import pytest

from atlas_api.clients.tickerbot_client import TickerbotClient
from atlas_api.tools import (
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

QUERY = "asset_type = 'CS' AND market_cap >= 10000000000"


@pytest.fixture
def provider_response() -> dict[str, object]:
    return {
        "as_of": "2026-08-26T20:00:00.000Z",
        "count": 1,
        "next_cursor": None,
        "results": [
            {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "asset_class": "stocks",
                "asset_type": "CS",
                "price": 225.0,
                "market_cap": 3_400_000_000_000,
                "pe_ratio": 34.0,
            }
        ],
        "_meta": {"null_coverage": {}},
    }


def response_with_json(status_code: int, data) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=data,
        request=httpx.Request("POST", "https://api.tickerbot.io/v2/scan"),
    )


async def scan(client: TickerbotClient, *, cursor: str | None = None):
    return await client.scan(
        query=QUERY,
        order="market_cap",
        direction="desc",
        limit=25,
        columns=["pe_ratio"],
        cursor=cursor,
    )


@pytest.mark.asyncio
async def test_scan_calls_correct_endpoint(monkeypatch, provider_response) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_response))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    await scan(
        TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
    )

    post.assert_awaited_once()
    _, kwargs = post.call_args
    assert kwargs["url"] == "https://api.tickerbot.io/v2/scan"


@pytest.mark.asyncio
async def test_scan_sends_bearer_authentication(monkeypatch, provider_response) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_response))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    await scan(
        TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
    )

    _, kwargs = post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["headers"]["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_scan_sends_correct_request_body_without_cursor(
    monkeypatch, provider_response
) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_response))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    await scan(
        TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
    )

    _, kwargs = post.call_args
    assert kwargs["json"] == {
        "q": "asset_type = 'CS' AND market_cap >= 10000000000",
        "order": "market_cap",
        "dir": "desc",
        "limit": 25,
        "columns": ["pe_ratio"],
        "asset_class": ["stocks"],
    }
    assert "cursor" not in kwargs["json"]


@pytest.mark.asyncio
async def test_scan_passes_opaque_cursor_unchanged(
    monkeypatch, provider_response
) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_response))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    cursor = "opaque-provider-cursor"

    await scan(
        TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2"),
        cursor=cursor,
    )

    _, kwargs = post.call_args
    assert kwargs["json"]["cursor"] == cursor


@pytest.mark.asyncio
async def test_scan_returns_raw_provider_object(monkeypatch, provider_response) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_response))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    result = await scan(
        TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
    )

    assert result == provider_response
    assert result["results"][0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_scan_maps_timeout(monkeypatch) -> None:
    post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamTimeoutError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_rate_limit(monkeypatch) -> None:
    post = AsyncMock(return_value=response_with_json(429, {"error": "rate limited"}))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamRateLimitedError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_5xx(monkeypatch) -> None:
    post = AsyncMock(return_value=response_with_json(503, {"error": "unavailable"}))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamUnavailableError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 402, 403])
async def test_scan_maps_account_failures_as_upstream_unavailable(
    monkeypatch, status_code: int
) -> None:
    post = AsyncMock(
        return_value=response_with_json(status_code, {"error": "account problem"})
    )
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamUnavailableError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_bad_request_as_upstream_response_error(monkeypatch) -> None:
    post = AsyncMock(
        return_value=response_with_json(400, {"error": "bad provider field"})
    )
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamResponseError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_network_failure(monkeypatch) -> None:
    post = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamUnavailableError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_invalid_json(monkeypatch) -> None:
    response = httpx.Response(
        200,
        content=b"not-json",
        request=httpx.Request("POST", "https://api.tickerbot.io/v2/scan"),
    )
    post = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamResponseError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_payload",
    [
        [],
        {"results": {}},
        {"results": ["AAPL"]},
    ],
)
async def test_scan_rejects_malformed_response_envelope(
    monkeypatch, provider_payload
) -> None:
    post = AsyncMock(return_value=response_with_json(200, provider_payload))
    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    with pytest.raises(UpstreamResponseError):
        await scan(
            TickerbotClient(api_key="test-key", base_url="https://api.tickerbot.io/v2")
        )


@pytest.mark.asyncio
async def test_scan_maps_unexpected_http_error(
    monkeypatch,
) -> None:
    post = AsyncMock(
        return_value=response_with_json(
            404,
            {"error": "not found"},
        )
    )
    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        post,
    )

    with pytest.raises(UpstreamResponseError):
        await scan(
            TickerbotClient(
                api_key="test-key",
                base_url="https://api.tickerbot.io/v2",
            )
        )
