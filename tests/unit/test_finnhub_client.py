from datetime import date
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
async def test_get_quote_returns_json_and_preserves_service_normalized_symbol(
    monkeypatch,
) -> None:
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
    assert kwargs["params"] == {"symbol": "aapl"}
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}
    assert kwargs["timeout"] == 10.0


@pytest.mark.asyncio
async def test_get_company_profile_returns_profile_data(monkeypatch) -> None:
    profile = {"name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"}
    response = httpx.Response(
        200,
        json=profile,
        request=httpx.Request("GET", "https://finnhub.io/api/v1/stock/profile2"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    result = await FinnhubClient(api_key="test-key").get_company_profile("AAPL")

    assert result == profile
    _, kwargs = get.call_args
    assert kwargs["params"] == {"symbol": "AAPL"}
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}


@pytest.mark.asyncio
async def test_get_basic_financials_uses_metric_endpoint_and_returns_raw_object(
    monkeypatch,
) -> None:
    financials = {"metric": {"peTTM": 31.82, "epsTTM": 6.42}}
    response = httpx.Response(
        200,
        json=financials,
        request=httpx.Request("GET", "https://finnhub.io/api/v1/stock/metric"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    result = await FinnhubClient(api_key="test-key").get_basic_financials("AAPL")

    assert result == financials
    get.assert_awaited_once()
    args, kwargs = get.call_args
    assert args[0] == "https://finnhub.io/api/v1/stock/metric"
    assert kwargs["params"] == {"symbol": "AAPL", "metric": "all"}
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}
    assert kwargs["timeout"] == 10.0


@pytest.mark.asyncio
async def test_get_company_news_uses_date_params_and_returns_raw_list(
    monkeypatch,
) -> None:
    news = [
        {
            "id": 123456,
            "headline": "Apple announces results",
            "datetime": 1_724_497_200,
        }
    ]
    response = httpx.Response(
        200,
        json=news,
        request=httpx.Request("GET", "https://finnhub.io/api/v1/company-news"),
    )
    get = AsyncMock(return_value=response)
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    result = await FinnhubClient(api_key="test-key").get_company_news(
        "AAPL",
        date(2026, 8, 17),
        date(2026, 8, 24),
    )

    assert result == news
    get.assert_awaited_once()
    args, kwargs = get.call_args
    assert args[0] == "https://finnhub.io/api/v1/company-news"
    assert kwargs["params"] == {
        "symbol": "AAPL",
        "from": "2026-08-17",
        "to": "2026-08-24",
    }
    assert kwargs["headers"] == {"X-Finnhub-Token": "test-key"}
    assert kwargs["timeout"] == 10.0


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "get_company_profile"])
async def test_client_maps_timeout(monkeypatch, method_name: str) -> None:
    get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamTimeoutError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")


@pytest.mark.asyncio
@pytest.mark.parametrize("method_name", ["get_quote", "get_company_profile"])
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
@pytest.mark.parametrize("method_name", ["get_quote", "get_company_profile"])
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
@pytest.mark.parametrize("method_name", ["get_quote", "get_company_profile"])
async def test_client_maps_request_error(monkeypatch, method_name: str) -> None:
    get = AsyncMock(side_effect=httpx.ConnectError("connection failed"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    with pytest.raises(UpstreamUnavailableError):
        await getattr(FinnhubClient(api_key="test-key"), method_name)("AAPL")
