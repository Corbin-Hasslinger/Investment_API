
from decimal import Decimal
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class StockQuote(BaseModel):
    symbol: str 
    current_price: Decimal
    price_change: Decimal
    percent_change: Decimal
    high_price: Decimal
    low_price: Decimal
    open_price: Decimal
    previous_close_price: Decimal
    timestamp: int

class ScreenerMetric(StrEnum):
    MARKET_CAP= "market_cap"
    PE_RATIO_TTM= "pe_ratio_ttm"
    PRICE_TO_BOOK= "price_to_book"
    PRICE_TO_SALES_TTM= "price_to_sales_ttm"
    PRICE_TO_FREE_CASH_FLOW_TTM= "price_to_free_cash_flow_ttm"

    REVENUE_GROWTH_YOY_PERCENT= "revenue_growth_yoy_percent"

    RETURN_ON_EQUITY_TTM_PERCENT= "return_on_equity_ttm_percent"
    OPERATING_MARGIN_TTM_PERCENT= "operating_margin_ttm_percent"
    NET_MARGIN_TTM_PERCENT= "net_margin_ttm_percent"

    CURRENT_RATIO= "current_ratio"
    DEBT_TO_EQUITY= "debt_to_equity"

    BETA= "beta"
    RETURN_1_YEAR_PERCENT= "return_1_year_percent"

class ScreenerOperator(StrEnum):
    EQ= "eq"
    GT= "gt"
    LT= "lt"
    GTE= "gte"
    LTE= "lte"

class SortDirection(StrEnum):
    ASC= "asc"
    DESC= "desc"

class StockScreenerCriterion(BaseModel):
    metric: ScreenerMetric
    operator: ScreenerOperator
    value: Decimal

    @field_validator("value")
    def validate_finite_value(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("Value must be finite")
        return value

class StockScreenerRequest(BaseModel):
    criteria: list[StockScreenerCriterion] = Field(min_length=1, max_length=10, description="List of screener criteria")
    sort_by: ScreenerMetric = Field(default=ScreenerMetric.MARKET_CAP)
    sort_direction: SortDirection = Field(default=SortDirection.DESC)
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of results to return")
    cursor: str | None = None

class StockScreenerMetricsRead(BaseModel):
    market_cap: Decimal | None= None
    pe_ratio_ttm: Decimal | None= None
    price_to_book: Decimal | None= None
    price_to_sales_ttm: Decimal | None= None
    price_to_free_cash_flow_ttm: Decimal | None= None

    revenue_growth_yoy_percent: Decimal | None= None

    return_on_equity_ttm_percent: Decimal | None= None
    operating_margin_ttm_percent: Decimal | None= None
    net_margin_ttm_percent: Decimal | None= None

    current_ratio: Decimal | None= None
    debt_to_equity: Decimal | None= None

    beta: Decimal | None= None
    return_1_year_percent: Decimal | None= None

class ScreenerMetricCoverageRead(BaseModel):
    metric: ScreenerMetric
    in_scope: int = Field(ge=0)
    evaluable: int = Field(ge=0)
    missing: int = Field(ge=0)

class StockScreenerResultRead(BaseModel):
    symbol: str
    name: str 
    price: Decimal | None= None
    day_change_percent: Decimal | None= None
    sector: str | None= None
    industry: str | None= None
    metrics: StockScreenerMetricsRead

class StockScreenerRead(BaseModel):
    as_of: AwareDatetime
    returned_count: int = Field(ge=0)
    next_cursor: str | None = None
    results: list[StockScreenerResultRead] = Field(default_factory=list)
    coverage: list[ScreenerMetricCoverageRead] = Field(default_factory=list)