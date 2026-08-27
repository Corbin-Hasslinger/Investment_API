from decimal import Decimal

import pytest
from pydantic import ValidationError

from atlas_api.schemas.stock import (
    ScreenerMetric,
    ScreenerOperator,
    SortDirection,
    StockScreenerCriterion,
    StockScreenerRequest,
)


def valid_criterion(
    *,
    metric: ScreenerMetric = ScreenerMetric.MARKET_CAP,
    operator: ScreenerOperator = ScreenerOperator.GTE,
    value: Decimal = Decimal("1000000000.00"),
) -> StockScreenerCriterion:
    return StockScreenerCriterion(metric=metric, operator=operator, value=value)


def test_one_valid_criterion_is_accepted() -> None:
    request = StockScreenerRequest(criteria=[valid_criterion()])

    assert len(request.criteria) == 1
    assert request.criteria[0] == StockScreenerCriterion(
        metric=ScreenerMetric.MARKET_CAP,
        operator=ScreenerOperator.GTE,
        value=Decimal("1000000000.00"),
    )


def test_multiple_valid_criteria_are_accepted() -> None:
    request = StockScreenerRequest(
        criteria=[
            valid_criterion(
                metric=ScreenerMetric.MARKET_CAP,
                operator=ScreenerOperator.GTE,
                value=Decimal(1000000000),
            ),
            valid_criterion(
                metric=ScreenerMetric.BETA,
                operator=ScreenerOperator.LT,
                value=Decimal("1.25"),
            ),
            valid_criterion(
                metric=ScreenerMetric.PE_RATIO_TTM,
                operator=ScreenerOperator.LTE,
                value=Decimal(30),
            ),
        ]
    )

    assert [criterion.metric for criterion in request.criteria] == [
        ScreenerMetric.MARKET_CAP,
        ScreenerMetric.BETA,
        ScreenerMetric.PE_RATIO_TTM,
    ]
    assert [criterion.operator for criterion in request.criteria] == [
        ScreenerOperator.GTE,
        ScreenerOperator.LT,
        ScreenerOperator.LTE,
    ]


@pytest.mark.parametrize("criteria", [[], [valid_criterion()] * 11])
def test_criteria_count_must_be_between_one_and_ten(
    criteria: list[StockScreenerCriterion],
) -> None:
    with pytest.raises(ValidationError):
        StockScreenerRequest(criteria=criteria)


def test_ten_criteria_is_the_valid_upper_boundary() -> None:
    request = StockScreenerRequest(criteria=[valid_criterion()] * 10)

    assert len(request.criteria) == 10


@pytest.mark.parametrize("limit", [1, 100])
def test_limit_boundaries_are_valid(limit: int) -> None:
    request = StockScreenerRequest(criteria=[valid_criterion()], limit=limit)

    assert request.limit == limit


@pytest.mark.parametrize("metric", ["not_a_metric", "current_price", "marketCap"])
def test_invalid_metric_is_rejected(metric: str) -> None:
    with pytest.raises(ValidationError):
        StockScreenerRequest.model_validate(
            {"criteria": [{"metric": metric, "operator": "gte", "value": "1"}]}
        )


@pytest.mark.parametrize("operator", ["between", "neq", "greater_than"])
def test_invalid_operator_is_rejected(operator: str) -> None:
    with pytest.raises(ValidationError):
        StockScreenerRequest.model_validate(
            {"criteria": [{"metric": "market_cap", "operator": operator, "value": "1"}]}
        )


@pytest.mark.parametrize(
    "value",
    [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")],
)
def test_non_finite_decimal_value_is_rejected(value: Decimal) -> None:
    with pytest.raises(ValidationError):
        StockScreenerRequest.model_validate(
            {
                "criteria": [
                    {
                        "metric": "market_cap",
                        "operator": "gte",
                        "value": value,
                    }
                ]
            }
        )


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_out_of_range_is_rejected(limit: int) -> None:
    with pytest.raises(ValidationError):
        StockScreenerRequest(criteria=[valid_criterion()], limit=limit)


def test_default_sort_direction_and_limit() -> None:
    request = StockScreenerRequest(criteria=[valid_criterion()])

    assert request.sort_by is ScreenerMetric.MARKET_CAP
    assert request.sort_direction is SortDirection.DESC
    assert request.limit == 25


@pytest.mark.parametrize("cursor", [None, "eyJvZmZzZXQiOjI1fQ"])
def test_cursor_accepts_none_or_string(cursor: str | None) -> None:
    request = StockScreenerRequest(criteria=[valid_criterion()], cursor=cursor)

    assert request.cursor == cursor
