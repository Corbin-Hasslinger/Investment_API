
from datetime import date
from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class CompanyOverviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(max_length=10, min_length=1, description="The stock symbol of the company")
    name: str = Field(max_length=50, min_length=1, description="The name of the company")
    exchange: str | None = Field(default=None, max_length=50, min_length=1, description="The exchange where the company is listed")
    industry: str | None = Field(default=None, max_length=50, min_length=1, description="The industry in which the company operates")
    country: str | None = Field(default=None, max_length=50, min_length=1, description="The country where the company is based")
    currency: str | None = Field(default=None, max_length=10, min_length=1, description="The currency in which the company's stock is traded")
    ipo_date: date | None = Field(default=None, description="The date when the company went public")
    website: str | None = Field(default=None, max_length=100, min_length=1, description="The website of the company")
    logo_url: str | None = Field(default=None, max_length=200, min_length=1, description="The URL of the company's logo")
    market_cap: Decimal | None = Field(default=None, description="The market capitalization of the company")
    shares_outstanding: Decimal | None = Field(default=None, description="The number of shares outstanding for the company")

class ValuationMetricsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pe_ratio_ttm: Decimal | None = Field(default=None, description="The price-to-earnings ratio (trailing twelve months)")
    price_to_book: Decimal | None = Field(default=None, description="The price-to-book ratio")
    price_to_sales_ttm: Decimal | None = Field(default=None, description="The price-to-sales ratio")
    price_to_free_cash_flow_ttm: Decimal | None = Field(default=None, description="The price-to-free-cash-flow ratio")

class PerformanceMetricsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fifty_two_week_high: Decimal | None = Field(default=None, description="The highest stock price in the last 52 weeks")
    fifty_two_week_low: Decimal | None = Field(default=None, description="The lowest stock price in the last 52 weeks")
    beta: Decimal | None = Field(default=None, description="The beta value of the stock, indicating its volatility relative to the market")

    return_3_month_percent: Decimal | None = Field(default=None, description="The stock's return over the past 3 months as a percentage")
    return_1_year_percent: Decimal | None = Field(default=None, description="The stock's return over the past 1 year as a percentage")

class FundamentalMetricsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eps_ttm: Decimal | None = Field(default=None, description="The earnings per share (trailing twelve months) of the company")

    revenue_growth_yoy_percent: Decimal | None = Field(default=None, description="The year-over-year revenue growth of the company as a percentage")
    eps_growth_yoy_percent: Decimal | None = Field(default=None, description="The year-over-year earnings per share growth of the company as a percentage")

    gross_margin_percent: Decimal | None = Field(default=None, description="The gross margin of the company as a percentage")
    operating_margin_percent: Decimal | None = Field(default=None, description="The operating margin of the company as a percentage")
    net_margin_percent: Decimal | None = Field(default=None, description="The net margin of the company as a percentage")

    return_on_equity_percent: Decimal | None = Field(default=None, description="The return on equity of the company as a percentage")

    current_ratio: Decimal | None = Field(default=None, description="The current ratio of the company")
    debt_to_equity: Decimal | None = Field(default=None, description="The debt-to-equity ratio of the company")

class CompanyNewsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    headline: str = Field(..., description="The headline of the news article")
    source: str = Field(..., description="The source of the news article")
    summary: str | None = Field(default=None, description="A brief summary of the news article")
    url: str = Field(..., description="The URL to the full news article")
    image_url: str | None = Field(default=None, description="The URL to the image associated with the news article")
    published_at: AwareDatetime = Field(..., description="The publication date and time of the news article")

class CompanyResearchRead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: CompanyOverviewRead
    valuation: ValuationMetricsRead
    performance: PerformanceMetricsRead
    fundamentals: FundamentalMetricsRead
    news: list[CompanyNewsRead] = Field(..., description="A list of news articles related to the company")
