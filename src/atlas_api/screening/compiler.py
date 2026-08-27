from decimal import Decimal

from atlas_api.schemas.stock import ScreenerOperator, StockScreenerCriterion
from atlas_api.screening.metrics import get_metric_definition

OPERATOR_MAP: dict[ScreenerOperator, str] = {
    ScreenerOperator.EQ: "=",
    ScreenerOperator.LT: "<",
    ScreenerOperator.LTE: "<=",
    ScreenerOperator.GT: ">",
    ScreenerOperator.GTE: ">=",
}

COMMON_STOCK_CONDITION = "asset_type = 'CS'"


def serialize_decimal(value: Decimal) -> str:
    return format(value, "f")


def compile_criterion(
    criterion: StockScreenerCriterion,
) -> str:
    definition = get_metric_definition(criterion.metric)

    provider_value = criterion.value * definition.input_scale
    operator = OPERATOR_MAP[criterion.operator]
    return f"{definition.provider_field} {operator} {serialize_decimal(provider_value)}"


class ScreenerQueryCompiler:
    def compile(
        self,
        criteria: list[StockScreenerCriterion],
    ) -> str:
        clauses = [COMMON_STOCK_CONDITION]

        clauses.extend(compile_criterion(criterion) for criterion in criteria)
        return " AND ".join(clauses)
