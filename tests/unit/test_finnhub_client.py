from unittest.mock import AsyncMock

import httpx
import pytest

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)


@pytest.mark.asyncio
async def test_get_quote_returns_json_and_sends_normalized_symbol(monkeypatch) -> None:
    response = httpx.Response(
        200,
        json={"c": 150.25},
        request=httpx.Request("GET", "https://finnhub.io/api/v1/quote"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    result = await FinnhubClient(api_key="test-key").get_quote("aapl")

    assert result == {"c": 150.25}
    get.assert_awaited_once()
    _, kwargs = get.call_args
    assert kwargs["params"] == {"symbol": "AAPL"}
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}
    assert kwargs["timeout"] == 10.0


@pytest.mark.asyncio
async def test_symbol_lookup_returns_profile_data(monkeypatch) -> None:
    profile = {"name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"}
    response = httpx.Response(
        200,
        json=profile,
        request=httpx.Request("GET", "https://finnhub.io/api/v1/stock/profile2"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    result = await FinnhubClient(api_key="test-key").symbol_lookup("AAPL")

    assert result == profile
    _, kwargs = get.call_args
    assert kwargs["params"] == {"symbol": "AAPL"}
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "symbol_lookup"])
async def test_client_maps_timeout(monkeypatch, method_name: str) -> None:
    get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamTimeoutError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "symbol_lookup"])
async def test_client_maps_rate_limit(monkeypatch, method_name: str) -> None:
    response = httpx.Response(
        429,
        request=httpx.Request("GET", "https://finnhub.io/api/v1"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamRateLimitedError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "symbol_lookup"])
async def test_client_maps_upstream_5xx(monkeypatch, method_name: str) -> None:
    response = httpx.Response(
        503,
        request=httpx.Request("GET", "https://finnhub.io/api/v1"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamUnavailableError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "symbol_lookup"])
async def test_client_maps_request_error(monkeypatch, method_name: str) -> None:
    get = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamUnavailableError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")
