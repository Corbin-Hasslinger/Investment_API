from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from atlas_api.clients.tickerbot_client import TickerbotClient
from atlas_api.schemas.stock import (
    ScreenerMetric,
    ScreenerOperator,
    SortDirection,
    StockScreenerCriterion,
    StockScreenerRequest,
)
from atlas_api.screening.compiler import ScreenerQueryCompiler
from atlas_api.services.screener_service import (
    SCREENER_RESULT_COLUMNS,
    ScreenerService,
)
from atlas_api.tools.errors import UpstreamResponseError


def build_request(
    *,
    criteria: list[StockScreenerCriterion] | None = None,
    sort_by: ScreenerMetric = ScreenerMetric.PE_RATIO_TTM,
    sort_direction: SortDirection = SortDirection.ASC,
    limit: int = 10,
    cursor: str | None = "abc123",
) -> StockScreenerRequest:
    return StockScreenerRequest(
        criteria=criteria
        or [
            StockScreenerCriterion(
                metric=ScreenerMetric.PE_RATIO_TTM,
                operator=ScreenerOperator.LTE,
                value=Decimal(25),
            )
        ],
        sort_by=sort_by,
        sort_direction=sort_direction,
        limit=limit,
        cursor=cursor,
    )


def build_provider_response(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "as_of": "2026-08-27T18:00:00Z",
        "count": 1,
        "next_cursor": None,
        "results": [
            {
                "ticker": "TEST",
                "name": "Test Corporation",
                "price": 100.25,
                "day_change_pct": 0.025,
                "sector": "Technology",
                "industry": "Software",
                "market_cap": 10_000_000_000,
                "pe_ratio": 20.0,
                "price_to_book": 5.0,
                "price_to_sales": 4.0,
                "price_to_free_cash_flow": 15.0,
                "revenue_growth_yoy": 0.125,
                "return_on_equity_ttm": 0.18,
                "operating_margin_ttm": 0.25,
                "profit_margin_ttm": 0.20,
                "current_ratio": 1.5,
                "debt_to_equity": 0.8,
                "beta": 1.1,
                "change_1y": 0.30,
            }
        ],
        "_meta": {
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "asset_type": {"null_rows": 0, "evaluable_rows": 5000},
                    "pe_ratio": {"null_rows": 500, "evaluable_rows": 4500},
                },
            },
        },
    }
    base.update(overrides)
    return base


@pytest.fixture
def tickerbot_client() -> AsyncMock:
    client = AsyncMock(spec=TickerbotClient)
    client.scan = AsyncMock(return_value=build_provider_response())
    return client


@pytest.fixture
def service(tickerbot_client: AsyncMock) -> ScreenerService:
    return ScreenerService(
        tickerbot_client=tickerbot_client,
        query_compiler=ScreenerQueryCompiler(),
    )


@pytest.mark.asyncio
async def test_screen_stocks_calls_client_with_exact_arguments(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    await service.screen_stocks(build_request())

    tickerbot_client.scan.assert_awaited_once_with(
        query="asset_type = 'CS' AND pe_ratio <= 25",
        order="pe_ratio",
        direction="asc",
        limit=10,
        cursor="abc123",
        columns=SCREENER_RESULT_COLUMNS,
    )


@pytest.mark.asyncio
async def test_screen_stocks_transforms_basic_result_fields(
    service: ScreenerService,
) -> None:
    result = await service.screen_stocks(build_request())

    assert result.returned_count == 1
    assert result.next_cursor is None
    assert result.as_of == datetime(2026, 8, 27, 18, 0, tzinfo=UTC)
    row = result.results[0]
    assert row.symbol == "TEST"
    assert row.name == "Test Corporation"
    assert row.day_change_percent == Decimal("2.5")
    assert row.metrics.pe_ratio_ttm == Decimal("20.0")


@pytest.mark.asyncio
async def test_screen_stocks_converts_every_percentage_metric(
    service: ScreenerService,
) -> None:
    result = await service.screen_stocks(build_request())

    metrics = result.results[0].metrics
    assert metrics.revenue_growth_yoy_percent == Decimal("12.5")
    assert metrics.return_on_equity_ttm_percent == Decimal(18)
    assert metrics.operating_margin_ttm_percent == Decimal(25)
    assert metrics.net_margin_ttm_percent == Decimal(20)
    assert metrics.return_1_year_percent == Decimal("30.00")


@pytest.mark.asyncio
async def test_screen_stocks_preserves_none_for_missing_metrics(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    row = {
        "ticker": "TEST",
        "name": "Test Corporation",
        "price": None,
        "day_change_pct": None,
        "sector": None,
        "industry": None,
        "pe_ratio": None,
        "price_to_book": None,
    }
    tickerbot_client.scan.return_value = build_provider_response(results=[row])

    result = await service.screen_stocks(build_request())

    metrics = result.results[0].metrics
    assert metrics.pe_ratio_ttm is None
    assert metrics.price_to_book is None
    assert result.results[0].price is None
    assert result.results[0].day_change_percent is None
    assert result.results[0].sector is None


@pytest.mark.asyncio
async def test_screen_stocks_translates_coverage_entries(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "asset_type": {"null_rows": 0, "evaluable_rows": 5000},
                    "market_cap": {"null_rows": 800, "evaluable_rows": 4200},
                },
            }
        }
    )
    request = build_request(
        criteria=[
            StockScreenerCriterion(
                metric=ScreenerMetric.MARKET_CAP,
                operator=ScreenerOperator.GTE,
                value=Decimal(1_000_000_000),
            )
        ],
        sort_by=ScreenerMetric.MARKET_CAP,
    )

    result = await service.screen_stocks(request)

    assert len(result.coverage) == 1
    coverage = result.coverage[0]
    assert coverage.metric == ScreenerMetric.MARKET_CAP
    assert coverage.in_scope == 5000
    assert coverage.evaluable == 4200
    assert coverage.missing == 800


@pytest.mark.asyncio
async def test_screen_stocks_hides_internal_predicate_coverage(
    service: ScreenerService,
) -> None:
    request = build_request(
        criteria=[
            StockScreenerCriterion(
                metric=ScreenerMetric.PE_RATIO_TTM,
                operator=ScreenerOperator.LTE,
                value=Decimal(25),
            )
        ]
    )

    result = await service.screen_stocks(request)

    assert {entry.metric for entry in result.coverage} == {ScreenerMetric.PE_RATIO_TTM}


@pytest.mark.asyncio
async def test_screen_stocks_deduplicates_repeated_metric_coverage(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "asset_type": {"null_rows": 0, "evaluable_rows": 5000},
                    "market_cap": {"null_rows": 800, "evaluable_rows": 4200},
                },
            }
        }
    )
    request = build_request(
        criteria=[
            StockScreenerCriterion(
                metric=ScreenerMetric.MARKET_CAP,
                operator=ScreenerOperator.GTE,
                value=Decimal(1_000_000_000),
            ),
            StockScreenerCriterion(
                metric=ScreenerMetric.MARKET_CAP,
                operator=ScreenerOperator.LTE,
                value=Decimal(100_000_000_000),
            ),
        ],
        sort_by=ScreenerMetric.MARKET_CAP,
    )

    result = await service.screen_stocks(request)

    assert len(result.coverage) == 1
    assert result.coverage[0].metric == ScreenerMetric.MARKET_CAP


@pytest.mark.asyncio
async def test_screen_stocks_preserves_opaque_next_cursor(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        next_cursor="opaque-value-123"
    )

    result = await service.screen_stocks(build_request())

    assert result.next_cursor == "opaque-value-123"


@pytest.mark.asyncio
async def test_screen_stocks_rejects_invalid_ticker_type(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        results=[{"ticker": 12345, "name": "Test Corporation"}]
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
async def test_screen_stocks_rejects_invalid_metric_value_shape(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        results=[
            {
                "ticker": "TEST",
                "name": "Test Corporation",
                "market_cap": {"weird": "object"},
            }
        ]
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
async def test_screen_stocks_rejects_missing_requested_coverage(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "asset_type": {
                        "null_rows": 0,
                        "evaluable_rows": 5000,
                    }
                },
            }
        }
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "null_coverage",
    [
        {
            "in_scope_rows": -1,
            "columns": {
                "pe_ratio": {"null_rows": 500, "evaluable_rows": 4500},
            },
        },
        {
            "in_scope_rows": 5000,
            "columns": {
                "pe_ratio": {"null_rows": -1, "evaluable_rows": 5001},
            },
        },
        {
            "in_scope_rows": 5000,
            "columns": {
                "pe_ratio": {"null_rows": 5001, "evaluable_rows": -1},
            },
        },
    ],
)
async def test_screen_stocks_rejects_negative_coverage_counts(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
    null_coverage: dict[str, object],
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={"null_coverage": null_coverage}
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
async def test_screen_stocks_rejects_inconsistent_coverage_counts(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={
            "null_coverage": {
                "in_scope_rows": 5000,
                "columns": {
                    "pe_ratio": {"null_rows": 500, "evaluable_rows": 4501},
                },
            }
        }
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
async def test_screen_stocks_sends_no_cursor_on_first_page(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    await service.screen_stocks(build_request(cursor=None))

    _, kwargs = tickerbot_client.scan.await_args
    assert kwargs["cursor"] is None


@pytest.mark.asyncio
async def test_screen_stocks_forwards_subsequent_page_cursor_exactly(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    await service.screen_stocks(build_request(cursor="abc123"))

    _, kwargs = tickerbot_client.scan.await_args
    assert kwargs["cursor"] == "abc123"


@pytest.mark.asyncio
async def test_coverage_arithmetic_matches_representative_provider_data(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        _meta={
            "null_coverage": {
                "in_scope_rows": 13889,
                "columns": {
                    "asset_type": {"null_rows": 0, "evaluable_rows": 13889},
                    "pe_ratio": {"null_rows": 11634, "evaluable_rows": 2255},
                },
            }
        }
    )

    result = await service.screen_stocks(build_request())

    coverage = result.coverage[0]
    assert coverage.in_scope == 13889
    assert coverage.evaluable == 2255
    assert coverage.missing == 11634
    assert coverage.evaluable + coverage.missing == coverage.in_scope


@pytest.mark.asyncio
async def test_screen_stocks_returns_200_shaped_result_for_zero_matches(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        count=0,
        next_cursor=None,
        results=[],
    )

    result = await service.screen_stocks(build_request())

    assert result.returned_count == 0
    assert result.next_cursor is None
    assert result.results == []


@pytest.mark.asyncio
async def test_screen_stocks_returns_none_for_every_optional_field_when_all_missing(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    row = {
        "ticker": "TEST",
        "name": "Test Corporation",
        "price": None,
        "day_change_pct": None,
        "sector": None,
        "industry": None,
        "market_cap": None,
        "pe_ratio": None,
        "price_to_book": None,
        "price_to_sales": None,
        "price_to_free_cash_flow": None,
        "revenue_growth_yoy": None,
        "return_on_equity_ttm": None,
        "operating_margin_ttm": None,
        "profit_margin_ttm": None,
        "current_ratio": None,
        "debt_to_equity": None,
        "beta": None,
        "change_1y": None,
    }
    tickerbot_client.scan.return_value = build_provider_response(results=[row])

    result = await service.screen_stocks(build_request())

    stock = result.results[0]
    assert stock.price is None
    assert stock.day_change_percent is None
    assert stock.sector is None
    assert stock.industry is None
    metrics = stock.metrics.model_dump()
    assert all(value is None for value in metrics.values())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_field", "value"),
    [
        ("pe_ratio", -12.5),
        ("revenue_growth_yoy", -0.30),
        ("profit_margin_ttm", -0.10),
        ("debt_to_equity", 15.0),
        ("current_ratio", 22.0),
        ("beta", -0.5),
    ],
)
async def test_screen_stocks_passes_through_strange_but_valid_financial_values(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
    provider_field: str,
    value: float,
) -> None:
    row = {"ticker": "TEST", "name": "Test Corporation", provider_field: value}
    tickerbot_client.scan.return_value = build_provider_response(results=[row])

    result = await service.screen_stocks(build_request())

    assert result.results[0] is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("nonfinite_value", [float("nan"), float("inf"), float("-inf")])
async def test_screen_stocks_rejects_nonfinite_provider_values(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
    nonfinite_value: float,
) -> None:
    row = {"ticker": "TEST", "name": "Test Corporation", "pe_ratio": nonfinite_value}
    tickerbot_client.scan.return_value = build_provider_response(results=[row])

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "as_of_value",
    [
        "2026-08-27T21:18:10.274000Z",
        "2026-08-27T21:18:10+00:00",
    ],
)
async def test_screen_stocks_accepts_valid_aware_as_of_variants(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
    as_of_value: str,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(as_of=as_of_value)

    result = await service.screen_stocks(build_request())

    assert result.as_of.tzinfo is not None


@pytest.mark.asyncio
async def test_screen_stocks_rejects_unparsable_as_of(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(as_of="banana")

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


@pytest.mark.asyncio
async def test_screen_stocks_rejects_timezone_naive_as_of(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
) -> None:
    tickerbot_client.scan.return_value = build_provider_response(
        as_of="2026-08-27T21:18:10"
    )

    with pytest.raises(UpstreamResponseError):
        await service.screen_stocks(build_request())


def test_screener_result_columns_includes_sector_and_industry() -> None:
    assert "sector" in SCREENER_RESULT_COLUMNS
    assert "industry" in SCREENER_RESULT_COLUMNS


def test_screener_result_columns_includes_every_metric_field_except_market_cap() -> None:
    from atlas_api.screening.metrics import SCREENER_METRICS

    for metric, definition in SCREENER_METRICS.items():
        if definition.provider_field == "market_cap":
            assert definition.provider_field not in SCREENER_RESULT_COLUMNS
        else:
            assert definition.provider_field in SCREENER_RESULT_COLUMNS, metric


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sort_by", "expected_order"),
    [
        (ScreenerMetric.NET_MARGIN_TTM_PERCENT, "profit_margin_ttm"),
        (ScreenerMetric.PE_RATIO_TTM, "pe_ratio"),
        (ScreenerMetric.RETURN_1_YEAR_PERCENT, "change_1y"),
    ],
)
async def test_screen_stocks_translates_sort_by_for_renamed_metrics(
    service: ScreenerService,
    tickerbot_client: AsyncMock,
    sort_by: ScreenerMetric,
    expected_order: str,
) -> None:
    await service.screen_stocks(build_request(sort_by=sort_by))

    _, kwargs = tickerbot_client.scan.await_args
    assert kwargs["order"] == expected_order


def test_screener_service_has_no_database_dependency() -> None:
    import inspect

    signature = inspect.signature(ScreenerService.__init__)
    parameter_names = set(signature.parameters) - {"self"}
    assert parameter_names == {"tickerbot_client", "query_compiler"}

