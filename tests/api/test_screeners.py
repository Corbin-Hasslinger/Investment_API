from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_api.di import get_screener_service
from atlas_api.schemas.stock import (
    ScreenerMetric,
    StockScreenerMetricsRead,
    StockScreenerRead,
    StockScreenerRequest,
    StockScreenerResultRead,
)
from atlas_api.services.screener_service import ScreenerService
from atlas_api.tools.errors import (
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

VALID_PAYLOAD = {
    "criteria": [
        {
            "metric": "market_cap",
            "operator": "gte",
            "value": 10000000000,
        }
    ],
    "sort_by": "market_cap",
    "sort_direction": "desc",
    "limit": 25,
}


def build_screener_read() -> StockScreenerRead:
    return StockScreenerRead(
        as_of=datetime(2026, 8, 27, 18, 0, tzinfo=UTC),
        returned_count=1,
        next_cursor=None,
        results=[
            StockScreenerResultRead(
                symbol="TEST",
                name="Test Corporation",
                metrics=StockScreenerMetricsRead(
                    market_cap=Decimal(10000000000),
                ),
            )
        ],
        coverage=[],
    )


def override_screener_service(override_dependency) -> MagicMock:
    service = MagicMock(spec=ScreenerService)
    service.screen_stocks = AsyncMock()
    override_dependency(get_screener_service, lambda: service)
    return service


def test_screen_stocks_returns_200_and_serializes_response(
    client, override_dependency
) -> None:
    service = override_screener_service(override_dependency)
    service.screen_stocks.return_value = build_screener_read()

    response = client.post("/screeners/stocks", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["returned_count"] == 1
    assert body["results"][0]["symbol"] == "TEST"
    service.screen_stocks.assert_awaited_once()


def test_screen_stocks_parses_request_into_typed_model_before_calling_service(
    client, override_dependency
) -> None:
    service = override_screener_service(override_dependency)
    service.screen_stocks.return_value = build_screener_read()

    client.post("/screeners/stocks", json=VALID_PAYLOAD)

    request = service.screen_stocks.await_args.args[0]
    assert isinstance(request, StockScreenerRequest)
    assert request.criteria[0].metric == ScreenerMetric.MARKET_CAP


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID_PAYLOAD, "criteria": []},
        {
            **VALID_PAYLOAD,
            "criteria": [
                {"metric": "not_a_real_metric", "operator": "gte", "value": 10}
            ],
        },
        {
            **VALID_PAYLOAD,
            "criteria": [{"metric": "market_cap", "operator": "banana", "value": 10}],
        },
        {**VALID_PAYLOAD, "limit": 101},
    ],
)
def test_screen_stocks_returns_422_for_invalid_requests(
    client, override_dependency, payload: dict[str, object]
) -> None:
    service = override_screener_service(override_dependency)

    response = client.post("/screeners/stocks", json=payload)

    assert response.status_code == 422
    service.screen_stocks.assert_not_called()


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (UpstreamTimeoutError("Tickerbot request timed out."), 504, "upstream_timeout"),
        (
            UpstreamRateLimitedError("Tickerbot rate limit exceeded."),
            429,
            "upstream_rate_limited",
        ),
        (
            UpstreamUnavailableError("Tickerbot service unavailable."),
            503,
            "upstream_unavailable",
        ),
        (
            UpstreamResponseError("Tickerbot returned an invalid response."),
            502,
            "upstream_response_error",
        ),
    ],
)
def test_screen_stocks_maps_service_errors_to_http_responses(
    client,
    override_dependency,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = override_screener_service(override_dependency)
    service.screen_stocks.side_effect = error

    response = client.post("/screeners/stocks", json=VALID_PAYLOAD)

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
