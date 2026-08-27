from dataclasses import dataclass
from decimal import Decimal

from atlas_api.schemas.stock import ScreenerMetric

PERCENT_TO_RATIO = Decimal("0.01")
RATIO_TO_PERCENT = Decimal(100)
NO_SCALE = Decimal(1)

@dataclass(frozen=True)
class ScreenerMetricDefinition:
    provider_field: str
    input_scale: Decimal = NO_SCALE
    output_scale: Decimal = NO_SCALE

SCREENER_METRICS: dict[ScreenerMetric,
                       ScreenerMetricDefinition
] = {
    ScreenerMetric.MARKET_CAP: ScreenerMetricDefinition(
        provider_field="market_cap",
    ),
    ScreenerMetric.PE_RATIO_TTM: ScreenerMetricDefinition(
        provider_field="pe_ratio",
    ),
    ScreenerMetric.PRICE_TO_BOOK: ScreenerMetricDefinition(
        provider_field="price_to_book",
    ),
    ScreenerMetric.PRICE_TO_SALES_TTM: ScreenerMetricDefinition(
        provider_field="price_to_sales",
    ),
    ScreenerMetric.PRICE_TO_FREE_CASH_FLOW_TTM: ScreenerMetricDefinition(
        provider_field="price_to_free_cash_flow",
    ),
    ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT: ScreenerMetricDefinition(
        provider_field="revenue_growth_yoy",
        input_scale=PERCENT_TO_RATIO,
        output_scale=RATIO_TO_PERCENT,
    ),
    ScreenerMetric.RETURN_ON_EQUITY_TTM_PERCENT: ScreenerMetricDefinition(
        provider_field="return_on_equity_ttm",
        input_scale=PERCENT_TO_RATIO,
        output_scale=RATIO_TO_PERCENT,
    ),
    ScreenerMetric.OPERATING_MARGIN_TTM_PERCENT: ScreenerMetricDefinition(
        provider_field="operating_margin_ttm",
        input_scale=PERCENT_TO_RATIO,
        output_scale=RATIO_TO_PERCENT,
    ),
    ScreenerMetric.NET_MARGIN_TTM_PERCENT: ScreenerMetricDefinition(
        provider_field="profit_margin_ttm",
        input_scale=PERCENT_TO_RATIO,
        output_scale=RATIO_TO_PERCENT,
    ),
    ScreenerMetric.CURRENT_RATIO: ScreenerMetricDefinition(
        provider_field="current_ratio",
    ),
    ScreenerMetric.DEBT_TO_EQUITY: ScreenerMetricDefinition(
        provider_field="debt_to_equity",
    ),
    ScreenerMetric.BETA: ScreenerMetricDefinition(
        provider_field="beta",
    ),
    ScreenerMetric.RETURN_1_YEAR_PERCENT: ScreenerMetricDefinition(
        provider_field="change_1y",
        input_scale=NO_SCALE,
        output_scale=NO_SCALE,
    ),
}
def get_metric_definition(
        metric: ScreenerMetric,
) -> ScreenerMetricDefinition:
    return SCREENER_METRICS[metric]

def get_provider_field(
        metric: ScreenerMetric,
) -> str:
    return SCREENER_METRICS[metric].provider_field

