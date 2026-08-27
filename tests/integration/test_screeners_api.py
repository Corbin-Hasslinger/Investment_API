from unittest.mock import AsyncMock, MagicMock

from atlas_api.clients.tickerbot_client import TickerbotClient
from atlas_api.di import get_tickerbot_client
from atlas_api.services.screener_service import SCREENER_RESULT_COLUMNS


def build_provider_response(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "as_of": "2026-08-27T18:00:00Z",
        "count": 1,
        "next_cursor": None,
        "results": [
            {
                "ticker": "TEST",
                "name": "Test Corporation",
                "price": 100,
                "day_change_pct": 0.02,
                "market_cap": 10_000_000_000,
                "pe_ratio": 20.0,
            }
        ],
        "_meta": {
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "market_cap": {"null_rows": 0, "evaluable_rows": 5000},
                    "pe_ratio": {"null_rows": 500, "evaluable_rows": 4500},
                },
            },
        },
    }
    base.update(overrides)
    return base


def override_tickerbot_client(override_dependency) -> MagicMock:
    client = MagicMock(spec=TickerbotClient)
    client.scan = AsyncMock(return_value=build_provider_response())
    override_dependency(get_tickerbot_client, lambda: client)
    return client


def test_screen_stocks_wires_real_service_and_compiler_to_mocked_tickerbot_client(
    client, override_dependency
) -> None:
    tickerbot_client = override_tickerbot_client(override_dependency)

    response = client.post(
        "/screeners/stocks",
        json={
            "criteria": [
                {"metric": "market_cap", "operator": "gte", "value": 10000000000},
                {"metric": "pe_ratio_ttm", "operator": "lte", "value": 25},
            ],
            "sort_by": "market_cap",
            "sort_direction": "desc",
            "limit": 25,
        },
    )

    assert response.status_code == 200
    tickerbot_client.scan.assert_awaited_once_with(
        query="asset_type = 'CS' AND market_cap >= 10000000000 AND pe_ratio <= 25",
        order="market_cap",
        direction="desc",
        limit=25,
        columns=SCREENER_RESULT_COLUMNS,
        cursor=None,
    )


def test_screen_stocks_returns_normalized_http_response(
    client, override_dependency
) -> None:
    override_tickerbot_client(override_dependency)

    response = client.post(
        "/screeners/stocks",
        json={
            "criteria": [
                {"metric": "market_cap", "operator": "gte", "value": 10000000000}
            ],
            "sort_by": "market_cap",
            "sort_direction": "desc",
            "limit": 25,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["returned_count"] == 1
    assert body["results"][0]["symbol"] == "TEST"
    assert body["results"][0]["day_change_percent"] == "2.00"


def test_screen_stocks_passes_cursor_through_the_whole_stack(
    client, override_dependency
) -> None:
    tickerbot_client = override_tickerbot_client(override_dependency)
    tickerbot_client.scan.return_value = build_provider_response(
        next_cursor="next-opaque-cursor"
    )

    response = client.post(
        "/screeners/stocks",
        json={
            "criteria": [
                {"metric": "market_cap", "operator": "gte", "value": 1000000000}
            ],
            "sort_by": "market_cap",
            "sort_direction": "desc",
            "limit": 25,
            "cursor": "opaque-cursor",
        },
    )

    assert response.status_code == 200
    _, kwargs = tickerbot_client.scan.await_args
    assert kwargs["cursor"] == "opaque-cursor"
    assert response.json()["next_cursor"] == "next-opaque-cursor"


def test_screen_stocks_same_screen_next_page_preserves_everything_but_cursor(
    client, override_dependency
) -> None:
    tickerbot_client = override_tickerbot_client(override_dependency)
    tickerbot_client.scan.return_value = build_provider_response(next_cursor="page-two")
    request_payload = {
        "criteria": [{"metric": "market_cap", "operator": "gte", "value": 1000000000}],
        "sort_by": "market_cap",
        "sort_direction": "desc",
        "limit": 2,
    }

    first_response = client.post("/screeners/stocks", json=request_payload)

    assert first_response.status_code == 200
    assert first_response.json()["next_cursor"] == "page-two"
    first_kwargs = tickerbot_client.scan.await_args.kwargs

    tickerbot_client.scan.return_value = build_provider_response(next_cursor=None)
    second_response = client.post(
        "/screeners/stocks", json={**request_payload, "cursor": "page-two"}
    )

    assert second_response.status_code == 200
    second_kwargs = tickerbot_client.scan.await_args.kwargs

    assert second_kwargs["query"] == first_kwargs["query"]
    assert second_kwargs["order"] == first_kwargs["order"]
    assert second_kwargs["direction"] == first_kwargs["direction"]
    assert second_kwargs["limit"] == first_kwargs["limit"]
    assert first_kwargs["cursor"] is None
    assert second_kwargs["cursor"] == "page-two"


def test_screen_stocks_minimal_request_reaches_provider_with_defaults(
    client, override_dependency
) -> None:
    tickerbot_client = override_tickerbot_client(override_dependency)

    response = client.post(
        "/screeners/stocks",
        json={
            "criteria": [
                {"metric": "market_cap", "operator": "gte", "value": 1000000000}
            ]
        },
    )

    assert response.status_code == 200
    _, kwargs = tickerbot_client.scan.await_args
    assert kwargs["order"] == "market_cap"
    assert kwargs["direction"] == "desc"
    assert kwargs["limit"] == 25
    assert kwargs["cursor"] is None
