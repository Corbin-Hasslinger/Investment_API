import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict

from atlas_api.schemas.research import (
    FundamentalMetricsRead,
    PerformanceMetricsRead,
    ValuationMetricsRead,
)
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.research_service import ResearchService


class PortfolioPositionAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    shares: Decimal
    average_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_percent: Decimal | None
    allocation_percent: Decimal


class PortfolioAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: UUID
    name: str
    description: str | None
    data_retrieved_at: AwareDatetime
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_gain_loss: Decimal
    total_unrealized_gain_loss_percent: Decimal | None
    positions: list[PortfolioPositionAIContext]


class SecurityNewsAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    headline: str
    source: str
    summary: str | None
    published_at: AwareDatetime


class SecurityCompanyAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    name: str
    exchange: str | None
    industry: str | None
    country: str | None
    currency: str | None
    ipo_date: date | None
    market_cap: Decimal | None
    shares_outstanding: Decimal | None


class SecurityQuoteAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_price: Decimal
    price_change: Decimal
    percent_change: Decimal
    high_price: Decimal
    low_price: Decimal
    open_price: Decimal
    previous_close_price: Decimal


class SecurityAIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    data_retrieved_at: AwareDatetime
    company: SecurityCompanyAIContext
    quote: SecurityQuoteAIContext
    valuation: ValuationMetricsRead
    performance: PerformanceMetricsRead
    fundamentals: FundamentalMetricsRead
    news: list[SecurityNewsAIContext]


async def build_portfolio_ai_context(
    *,
    portfolio_id: UUID,
    user_id: UUID,
    portfolio_service: PortfolioService,
    portfolio_analytics_service: PortfolioAnalyticsService,
) -> PortfolioAIContext:
    portfolio = portfolio_service.get_portfolio(portfolio_id, user_id)
    analytics = await portfolio_analytics_service.get_portfolio_analytics(
        portfolio_id=portfolio_id, user_id=user_id
    )

    return PortfolioAIContext(
        portfolio_id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        data_retrieved_at=datetime.now(UTC),
        total_market_value=analytics.total_market_value,
        total_cost_basis=analytics.total_cost_basis,
        total_unrealized_gain_loss=analytics.total_unrealized_gain_loss,
        total_unrealized_gain_loss_percent=analytics.total_unrealized_gain_loss_percent,
        positions=[
            PortfolioPositionAIContext.model_validate(position.model_dump())
            for position in analytics.positions
        ],
    )


async def build_security_ai_context(
    *,
    symbol: str,
    research_service: ResearchService,
    market_data_service: MarketDataService,
) -> SecurityAIContext:
    research, quote = await asyncio.gather(
        research_service.get_company_research(symbol=symbol),
        market_data_service.get_quote(symbol=symbol),
    )

    return SecurityAIContext(
        symbol=research.company.symbol,
        data_retrieved_at=datetime.now(UTC),
        company=SecurityCompanyAIContext.model_validate(
            research.company.model_dump(exclude={"website", "logo_url"})
        ),
        quote=SecurityQuoteAIContext.model_validate(
            quote.model_dump(exclude={"symbol", "timestamp"})
        ),
        valuation=research.valuation,
        performance=research.performance,
        fundamentals=research.fundamentals,
        news=[
            SecurityNewsAIContext(
                headline=item.headline,
                source=item.source,
                summary=item.summary,
                published_at=item.published_at,
            )
            for item in research.news
        ],
    )
