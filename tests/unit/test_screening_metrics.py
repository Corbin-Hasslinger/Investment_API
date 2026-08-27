from decimal import Decimal

import pytest

from atlas_api.schemas.stock import ScreenerMetric, ScreenerOperator
from atlas_api.screening.compiler import OPERATOR_MAP
from atlas_api.screening.metrics import (
    NO_SCALE,
    PERCENT_TO_RATIO,
    RATIO_TO_PERCENT,
    SCREENER_METRICS,
)


def test_every_screener_metric_has_registry_definition() -> None:
    assert set(SCREENER_METRICS) == set(ScreenerMetric)


def test_every_screener_operator_has_mapping() -> None:
    assert set(OPERATOR_MAP) == set(ScreenerOperator)


@pytest.mark.parametrize(
    ("metric", "expected_provider_field"),
    [
        (ScreenerMetric.PE_RATIO_TTM, "pe_ratio"),
        (ScreenerMetric.PRICE_TO_SALES_TTM, "price_to_sales"),
        (ScreenerMetric.PRICE_TO_FREE_CASH_FLOW_TTM, "price_to_free_cash_flow"),
        (ScreenerMetric.NET_MARGIN_TTM_PERCENT, "profit_margin_ttm"),
        (ScreenerMetric.RETURN_1_YEAR_PERCENT, "change_1y"),
    ],
)
def test_provider_mappings_for_differently_named_metrics(
    metric: ScreenerMetric,
    expected_provider_field: str,
) -> None:
    assert SCREENER_METRICS[metric].provider_field == expected_provider_field


@pytest.mark.parametrize(
    "metric",
    [
        ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT,
        ScreenerMetric.RETURN_ON_EQUITY_TTM_PERCENT,
        ScreenerMetric.OPERATING_MARGIN_TTM_PERCENT,
        ScreenerMetric.NET_MARGIN_TTM_PERCENT,
        ScreenerMetric.RETURN_1_YEAR_PERCENT,
    ],
)
def test_percentage_metrics_convert_input_percent_to_provider_ratio(metric: ScreenerMetric) -> None:
    assert SCREENER_METRICS[metric].input_scale == PERCENT_TO_RATIO


def test_return_1_year_percent_uses_provider_native_scale() -> None:
    assert SCREENER_METRICS[ScreenerMetric.RETURN_1_YEAR_PERCENT].input_scale == NO_SCALE
    assert SCREENER_METRICS[ScreenerMetric.RETURN_1_YEAR_PERCENT].output_scale == NO_SCALE


@pytest.mark.parametrize(
    ("operator", "expected"),
    [
        (ScreenerOperator.EQ, "="),
        (ScreenerOperator.GT, ">"),
        (ScreenerOperator.GTE, ">="),
        (ScreenerOperator.LT, "<"),
        (ScreenerOperator.LTE, "<="),
    ],
)
def test_operator_mapping(operator: ScreenerOperator, expected: str) -> None:
    assert OPERATOR_MAP[operator] == expected


def test_market_cap_metric_is_not_scaled() -> None:
    assert SCREENER_METRICS[ScreenerMetric.MARKET_CAP].input_scale == Decimal(1)

def test_percentage_metrics_convert_provider_ratio_to_atlas_percent(
    metric: ScreenerMetric,
) -> None:
    assert SCREENER_METRICS[metric].output_scale == RATIO_TO_PERCENT