from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from atlas_api.ai.context import (
    PortfolioAIContext,
    SecurityAIContext,
    build_portfolio_ai_context,
    build_security_ai_context,
)
from atlas_api.schemas.analytics import (
    PortfolioAnalyticsRead,
    PortfolioPositionAnalyticsRead,
)
from atlas_api.schemas.portfolio import PortfolioRead
from atlas_api.schemas.research import (
    CompanyNewsRead,
    CompanyOverviewRead,
    CompanyResearchRead,
    FundamentalMetricsRead,
    PerformanceMetricsRead,
    ValuationMetricsRead,
)
from atlas_api.schemas.stock import StockQuote
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.research_service import ResearchService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    UpstreamTimeoutError,
)

PORTFOLIO_ID = uuid4()
USER_ID = uuid4()


def build_portfolio(**overrides) -> PortfolioRead:
    values = {
        "id": PORTFOLIO_ID,
        "user_id": USER_ID,
        "name": "Growth Portfolio",
        "description": "Long-term growth holdings",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 2, tzinfo=UTC),
    }
    return PortfolioRead(**{**values, **overrides})


def build_position(**overrides) -> PortfolioPositionAnalyticsRead:
    values = {
        "symbol": "AAPL",
        "shares": Decimal(10),
        "average_cost": Decimal(100),
        "current_price": Decimal(150),
        "market_value": Decimal(1500),
        "cost_basis": Decimal(1000),
        "unrealized_gain_loss": Decimal(500),
        "unrealized_gain_loss_percent": Decimal(50),
        "allocation_percent": Decimal(100),
    }
    return PortfolioPositionAnalyticsRead(**{**values, **overrides})


def build_analytics(**overrides) -> PortfolioAnalyticsRead:
    values = {
        "portfolio_id": PORTFOLIO_ID,
        "total_market_value": Decimal(1500),
        "total_cost_basis": Decimal(1000),
        "total_unrealized_gain_loss": Decimal(500),
        "total_unrealized_gain_loss_percent": Decimal(50),
        "positions": [build_position()],
    }
    return PortfolioAnalyticsRead(**{**values, **overrides})


def build_research(**overrides) -> CompanyResearchRead:
    values = {
        "company": CompanyOverviewRead(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            industry="Technology",
            country="US",
            currency="USD",
            ipo_date=date(1980, 12, 12),
            website="https://apple.com",
            logo_url="https://logos.example/aapl.png",
            market_cap=Decimal(3_000_000_000_000),
            shares_outstanding=Decimal(15_000_000_000),
        ),
        "valuation": ValuationMetricsRead(pe_ratio_ttm=Decimal(30)),
        "performance": PerformanceMetricsRead(beta=Decimal("1.2")),
        "fundamentals": FundamentalMetricsRead(eps_ttm=Decimal(6)),
        "news": [
            CompanyNewsRead(
                id=123,
                headline="Apple announces results",
                source="Reuters",
                summary="Quarterly results exceeded expectations.",
                url="https://news.example/article",
                image_url="https://news.example/image.png",
                published_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
            )
        ],
    }
    return CompanyResearchRead(**{**values, **overrides})


def build_quote(**overrides) -> StockQuote:
    values = {
        "symbol": "AAPL",
        "current_price": Decimal(150),
        "price_change": Decimal(5),
        "percent_change": Decimal("3.45"),
        "high_price": Decimal(152),
        "low_price": Decimal(147),
        "open_price": Decimal(148),
        "previous_close_price": Decimal(145),
        "timestamp": 1756500000,
    }
    return StockQuote(**{**values, **overrides})


@pytest.fixture
def portfolio_service() -> MagicMock:
    service = MagicMock(spec=PortfolioService)
    service.get_portfolio.return_value = build_portfolio()
    return service


@pytest.fixture
def portfolio_analytics_service() -> MagicMock:
    service = MagicMock(spec=PortfolioAnalyticsService)
    service.get_portfolio_analytics = AsyncMock(return_value=build_analytics())
    return service


@pytest.fixture
def research_service() -> MagicMock:
    service = MagicMock(spec=ResearchService)
    service.get_company_research = AsyncMock(return_value=build_research())
    return service


@pytest.fixture
def market_data_service() -> MagicMock:
    service = MagicMock(spec=MarketDataService)
    service.get_quote = AsyncMock(return_value=build_quote())
    return service


async def build_portfolio_context(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> PortfolioAIContext:
    return await build_portfolio_ai_context(
        portfolio_id=PORTFOLIO_ID,
        user_id=USER_ID,
        portfolio_service=portfolio_service,
        portfolio_analytics_service=portfolio_analytics_service,
    )


async def build_security_context(
    research_service: MagicMock,
    market_data_service: MagicMock,
    symbol: str = "aapl",
) -> SecurityAIContext:
    return await build_security_ai_context(
        symbol=symbol,
        research_service=research_service,
        market_data_service=market_data_service,
    )


@pytest.mark.asyncio
async def test_portfolio_context_calls_services_with_identity_arguments(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    await build_portfolio_context(portfolio_service, portfolio_analytics_service)

    portfolio_service.get_portfolio.assert_called_once_with(PORTFOLIO_ID, USER_ID)
    portfolio_analytics_service.get_portfolio_analytics.assert_awaited_once_with(
        portfolio_id=PORTFOLIO_ID, user_id=USER_ID
    )


@pytest.mark.asyncio
async def test_portfolio_context_copies_totals_exactly_from_analytics(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    analytics = build_analytics(
        total_market_value=Decimal("12345.67"),
        total_cost_basis=Decimal("10000.00"),
        total_unrealized_gain_loss=Decimal("2345.67"),
        total_unrealized_gain_loss_percent=Decimal("23.4567"),
    )
    portfolio_analytics_service.get_portfolio_analytics.return_value = analytics

    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert context.portfolio_id == PORTFOLIO_ID
    assert context.total_market_value == analytics.total_market_value
    assert context.total_cost_basis == analytics.total_cost_basis
    assert context.total_unrealized_gain_loss == analytics.total_unrealized_gain_loss
    assert (
        context.total_unrealized_gain_loss_percent
        == analytics.total_unrealized_gain_loss_percent
    )


@pytest.mark.asyncio
async def test_portfolio_context_copies_positions_exactly_from_analytics(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    analytics = build_analytics(
        positions=[
            build_position(symbol="AAPL", allocation_percent=Decimal(60)),
            build_position(
                symbol="MSFT",
                shares=Decimal(5),
                average_cost=Decimal(200),
                current_price=Decimal(180),
                market_value=Decimal(900),
                cost_basis=Decimal(1000),
                unrealized_gain_loss=Decimal(-100),
                unrealized_gain_loss_percent=Decimal(-10),
                allocation_percent=Decimal(40),
            ),
        ]
    )
    portfolio_analytics_service.get_portfolio_analytics.return_value = analytics

    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert [position.model_dump() for position in context.positions] == [
        position.model_dump() for position in analytics.positions
    ]


@pytest.mark.asyncio
async def test_portfolio_context_includes_name_and_description(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    portfolio_service.get_portfolio.return_value = build_portfolio(
        name="Retirement", description="Tax-advantaged holdings"
    )

    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert context.name == "Retirement"
    assert context.description == "Tax-advantaged holdings"


@pytest.mark.asyncio
async def test_portfolio_context_keeps_empty_positions_empty(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    portfolio_analytics_service.get_portfolio_analytics.return_value = build_analytics(
        total_market_value=Decimal(0),
        total_cost_basis=Decimal(0),
        total_unrealized_gain_loss=Decimal(0),
        total_unrealized_gain_loss_percent=None,
        positions=[],
    )

    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert context.positions == []


@pytest.mark.asyncio
async def test_portfolio_context_preserves_none_return_percent(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    portfolio_analytics_service.get_portfolio_analytics.return_value = build_analytics(
        total_unrealized_gain_loss_percent=None,
        positions=[build_position(unrealized_gain_loss_percent=None)],
    )

    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert context.total_unrealized_gain_loss_percent is None
    assert context.positions[0].unrealized_gain_loss_percent is None


@pytest.mark.asyncio
async def test_portfolio_context_data_retrieved_at_is_timezone_aware(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    context = await build_portfolio_context(
        portfolio_service, portfolio_analytics_service
    )

    assert context.data_retrieved_at.tzinfo is not None
    assert context.data_retrieved_at.utcoffset() is not None


@pytest.mark.asyncio
async def test_portfolio_context_propagates_ownership_errors(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    portfolio_service.get_portfolio.side_effect = PortfolioNotFoundError(
        "Portfolio not found"
    )

    with pytest.raises(PortfolioNotFoundError):
        await build_portfolio_context(portfolio_service, portfolio_analytics_service)

    portfolio_analytics_service.get_portfolio_analytics.assert_not_awaited()


@pytest.mark.asyncio
async def test_portfolio_context_performs_no_writes(
    portfolio_service: MagicMock,
    portfolio_analytics_service: MagicMock,
) -> None:
    await build_portfolio_context(portfolio_service, portfolio_analytics_service)

    called = {call[0] for call in portfolio_service.method_calls} | {
        call[0] for call in portfolio_analytics_service.method_calls
    }
    assert called == {"get_portfolio", "get_portfolio_analytics"}


@pytest.mark.asyncio
async def test_security_context_calls_research_and_quote_services(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    await build_security_context(research_service, market_data_service)

    research_service.get_company_research.assert_awaited_once_with(symbol="aapl")
    market_data_service.get_quote.assert_awaited_once_with(symbol="aapl")


@pytest.mark.asyncio
async def test_security_context_uses_normalized_symbol_from_research(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    context = await build_security_context(
        research_service, market_data_service, symbol="aapl"
    )

    assert context.symbol == "AAPL"
    assert context.company.symbol == "AAPL"


@pytest.mark.asyncio
async def test_security_context_includes_quote_fields(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    quote = build_quote()
    market_data_service.get_quote.return_value = quote

    context = await build_security_context(research_service, market_data_service)

    assert context.quote.model_dump() == quote.model_dump(
        exclude={"symbol", "timestamp"}
    )


@pytest.mark.asyncio
async def test_security_context_includes_metric_groups_unchanged(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    research = build_research()
    research_service.get_company_research.return_value = research

    context = await build_security_context(research_service, market_data_service)

    assert context.valuation == research.valuation
    assert context.performance == research.performance
    assert context.fundamentals == research.fundamentals


@pytest.mark.asyncio
async def test_security_context_trims_presentation_only_fields(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    context = await build_security_context(research_service, market_data_service)

    company_fields = set(context.company.model_dump())
    assert "website" not in company_fields
    assert "logo_url" not in company_fields

    news_fields = set(context.news[0].model_dump())
    assert news_fields == {"headline", "source", "summary", "published_at"}

    quote_fields = set(context.quote.model_dump())
    assert "symbol" not in quote_fields
    assert "timestamp" not in quote_fields


@pytest.mark.asyncio
async def test_security_context_preserves_none_metrics(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    research_service.get_company_research.return_value = build_research(
        company=CompanyOverviewRead(symbol="AAPL", name="Apple Inc."),
        valuation=ValuationMetricsRead(),
        performance=PerformanceMetricsRead(),
        fundamentals=FundamentalMetricsRead(),
    )

    context = await build_security_context(research_service, market_data_service)

    assert context.company.market_cap is None
    assert context.company.ipo_date is None
    assert context.valuation.pe_ratio_ttm is None
    assert context.performance.beta is None
    assert context.fundamentals.eps_ttm is None


@pytest.mark.asyncio
async def test_security_context_copies_news_values(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    research = build_research()
    research_service.get_company_research.return_value = research

    context = await build_security_context(research_service, market_data_service)

    article = research.news[0]
    assert context.news[0].model_dump() == {
        "headline": article.headline,
        "source": article.source,
        "summary": article.summary,
        "published_at": article.published_at,
    }


@pytest.mark.asyncio
async def test_security_context_data_retrieved_at_is_timezone_aware(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    context = await build_security_context(research_service, market_data_service)

    assert context.data_retrieved_at.tzinfo is not None
    assert context.data_retrieved_at.utcoffset() is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("failing_service", ["research", "quote"])
async def test_security_context_propagates_upstream_errors(
    research_service: MagicMock,
    market_data_service: MagicMock,
    failing_service: str,
) -> None:
    error = UpstreamTimeoutError("Upstream timed out.")
    if failing_service == "research":
        research_service.get_company_research.side_effect = error
    else:
        market_data_service.get_quote.side_effect = error

    with pytest.raises(UpstreamTimeoutError):
        await build_security_context(research_service, market_data_service)


@pytest.mark.asyncio
async def test_security_context_awaits_both_providers_once(
    research_service: MagicMock,
    market_data_service: MagicMock,
) -> None:
    await build_security_context(research_service, market_data_service)

    research_service.get_company_research.assert_awaited_once()
    market_data_service.get_quote.assert_awaited_once()
