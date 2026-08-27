from decimal import Decimal

import pytest
from pydantic import ValidationError

from atlas_api.schemas.stock import (
    ScreenerMetric,
    ScreenerOperator,
    StockScreenerCriterion,
)
from atlas_api.screening.compiler import (
    COMMON_STOCK_CONDITION,
    ScreenerQueryCompiler,
    compile_criterion,
    serialize_decimal,
)


def criterion(
    metric: ScreenerMetric,
    operator: ScreenerOperator,
    value: Decimal,
) -> StockScreenerCriterion:
    return StockScreenerCriterion(metric=metric, operator=operator, value=value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal(25), "25"),
        (Decimal("25.5"), "25.5"),
        (Decimal("1E+10"), "10000000000"),
        (Decimal(-5), "-5"),
        (Decimal("0.10"), "0.10"),
    ],
)
def test_decimal_serialization_is_deterministic_numeric_text(
    value: Decimal,
    expected: str,
) -> None:
    assert serialize_decimal(value) == expected


@pytest.mark.parametrize(
    ("test_criterion", "expected"),
    [
        (
            criterion(
                ScreenerMetric.MARKET_CAP,
                ScreenerOperator.GTE,
                Decimal(10_000_000_000),
            ),
            "market_cap >= 10000000000",
        ),
        (
            criterion(ScreenerMetric.PE_RATIO_TTM, ScreenerOperator.LT, Decimal(20)),
            "pe_ratio < 20",
        ),
        (
            criterion(
                ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT,
                ScreenerOperator.GTE,
                Decimal(10),
            ),
            "revenue_growth_yoy >= 0.10",
        ),
        (
            criterion(
                ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT,
                ScreenerOperator.GT,
                Decimal(-5),
            ),
            "revenue_growth_yoy > -0.05",
        ),
    ],
)
def test_compile_single_criterion(
    test_criterion: StockScreenerCriterion,
    expected: str,
) -> None:
    assert compile_criterion(test_criterion) == expected


def test_compile_query_with_one_criterion_starts_with_common_stock_condition() -> None:
    query = ScreenerQueryCompiler().compile(
        [criterion(ScreenerMetric.MARKET_CAP, ScreenerOperator.GTE, Decimal(1_000_000_000))]
    )

    assert query == "asset_type = 'CS' AND market_cap >= 1000000000"
    assert query.startswith(COMMON_STOCK_CONDITION)
    assert query.count(" AND ") == 1


def test_compile_query_preserves_criteria_order_and_single_and_between_clauses() -> None:
    query = ScreenerQueryCompiler().compile(
        [
            criterion(ScreenerMetric.MARKET_CAP, ScreenerOperator.GTE, Decimal(1_000_000_000)),
            criterion(ScreenerMetric.PE_RATIO_TTM, ScreenerOperator.LTE, Decimal(25)),
        ]
    )

    assert query == "asset_type = 'CS' AND market_cap >= 1000000000 AND pe_ratio <= 25"
    assert query.split(" AND ") == [
        "asset_type = 'CS'",
        "market_cap >= 1000000000",
        "pe_ratio <= 25",
    ]
    assert query.count(" AND ") == 2
    assert "pe_ratio_ttm" not in query


def test_compile_query_uses_provider_names_when_atlas_metric_names_differ() -> None:
    query = ScreenerQueryCompiler().compile(
        [
            criterion(ScreenerMetric.PRICE_TO_SALES_TTM, ScreenerOperator.LT, Decimal(5)),
            criterion(ScreenerMetric.RETURN_1_YEAR_PERCENT, ScreenerOperator.GTE, Decimal(12)),
        ]
    )

    assert "price_to_sales < 5" in query
    assert "change_1y >= 0.12" in query
    assert "price_to_sales_ttm" not in query
    assert "return_1_year_percent" not in query


def test_compiler_inputs_reject_arbitrary_metric_operator_and_value_fragments() -> None:
    with pytest.raises(ValidationError):
        StockScreenerCriterion.model_validate(
            {
                "metric": "market_cap; DROP TABLE security; --",
                "operator": "gte",
                "value": "1000000000",
            }
        )

    with pytest.raises(ValidationError):
        StockScreenerCriterion.model_validate(
            {
                "metric": "market_cap",
                "operator": ">= 0 OR 1=1 --",
                "value": "1000000000",
            }
        )

    with pytest.raises(ValidationError):
        StockScreenerCriterion.model_validate(
            {
                "metric": "market_cap",
                "operator": "gte",
                "value": "0 OR 1=1",
            }
        )


def test_compiler_output_uses_only_registry_and_serialized_decimal_fragments() -> None:
    query = ScreenerQueryCompiler().compile(
        [criterion(ScreenerMetric.NET_MARGIN_TTM_PERCENT, ScreenerOperator.GT, Decimal(-5))]
    )

    assert query == "asset_type = 'CS' AND profit_margin_ttm > -0.05"
    assert "net_margin_ttm_percent" not in query
    assert ";" not in query
    assert "--" not in query
