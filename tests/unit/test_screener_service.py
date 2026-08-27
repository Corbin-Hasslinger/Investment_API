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
    assert metrics.return_1_year_percent == Decimal("0.30")


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
