from decimal import Decimal

import pytest

from atlas_api.schemas.stock import (
    ScreenerMetric,
    ScreenerOperator,
    StockScreenerCriterion,
)
from atlas_api.screening.compiler import compile_criterion
from atlas_api.screening.metrics import get_metric_definition

# (metric, atlas_input, expected_provider_query_value, provider_result_value, expected_atlas_output)
ROUND_TRIP_CASES = [
    (
        ScreenerMetric.MARKET_CAP,
        Decimal(10_000_000_000),
        Decimal(10_000_000_000),
        Decimal(10_000_000_000),
        Decimal(10_000_000_000),
    ),
    (ScreenerMetric.PE_RATIO_TTM, Decimal(20), Decimal(20), Decimal(20), Decimal(20)),
    (ScreenerMetric.PRICE_TO_BOOK, Decimal(5), Decimal(5), Decimal(5), Decimal(5)),
    (ScreenerMetric.PRICE_TO_SALES_TTM, Decimal(4), Decimal(4), Decimal(4), Decimal(4)),
    (
        ScreenerMetric.PRICE_TO_FREE_CASH_FLOW_TTM,
        Decimal(15),
        Decimal(15),
        Decimal(15),
        Decimal(15),
    ),
    (
        ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT,
        Decimal(20),
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("20.00"),
    ),
    (
        ScreenerMetric.RETURN_ON_EQUITY_TTM_PERCENT,
        Decimal(18),
        Decimal("0.18"),
        Decimal("0.18"),
        Decimal("18.00"),
    ),
    (
        ScreenerMetric.OPERATING_MARGIN_TTM_PERCENT,
        Decimal(25),
        Decimal("0.25"),
        Decimal("0.25"),
        Decimal("25.00"),
    ),
    (
        ScreenerMetric.NET_MARGIN_TTM_PERCENT,
        Decimal(20),
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("20.00"),
    ),
    (
        ScreenerMetric.CURRENT_RATIO,
        Decimal("1.5"),
        Decimal("1.5"),
        Decimal("1.5"),
        Decimal("1.5"),
    ),
    (
        ScreenerMetric.DEBT_TO_EQUITY,
        Decimal("0.8"),
        Decimal("0.8"),
        Decimal("0.8"),
        Decimal("0.8"),
    ),
    (
        ScreenerMetric.BETA,
        Decimal("1.1"),
        Decimal("1.1"),
        Decimal("1.1"),
        Decimal("1.1"),
    ),
    (
        ScreenerMetric.RETURN_1_YEAR_PERCENT,
        Decimal(20),
        Decimal("0.20"),
        Decimal("0.20"),
        Decimal("20.00"),
    ),
]

# A metric added to the enum but missing here fails collection immediately, not silently at runtime.
assert {case[0] for case in ROUND_TRIP_CASES} == set(ScreenerMetric)


@pytest.mark.parametrize(
    (
        "metric",
        "atlas_input",
        "expected_provider_query_value",
        "provider_result_value",
        "expected_atlas_output",
    ),
    ROUND_TRIP_CASES,
)
def test_metric_round_trips_between_atlas_and_provider_units(
    metric: ScreenerMetric,
    atlas_input: Decimal,
    expected_provider_query_value: Decimal,
    provider_result_value: Decimal,
    expected_atlas_output: Decimal,
) -> None:
    criterion = StockScreenerCriterion(
        metric=metric, operator=ScreenerOperator.GTE, value=atlas_input
    )
    compiled = compile_criterion(criterion)
    compiled_value = Decimal(compiled.rsplit(" ", 1)[-1])
    assert compiled_value == expected_provider_query_value

    definition = get_metric_definition(metric)
    atlas_output = provider_result_value * definition.output_scale
    assert atlas_output == expected_atlas_output
