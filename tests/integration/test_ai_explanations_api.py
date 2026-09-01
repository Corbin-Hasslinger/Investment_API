from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.core.db import get_session
from atlas_api.di import get_current_user, get_finnhub_client, get_llm_client
from atlas_api.models.positions import Position
from atlas_api.schemas.ai import (
    PortfolioExplanationContent,
    SecurityExplanationContent,
)
from atlas_api.schemas.user import CurrentUserRead


def build_finnhub_client() -> MagicMock:
    finnhub_client = MagicMock(spec=FinnhubClient)
    finnhub_client.get_quote = AsyncMock(
        return_value={
            "c": 150.25,
            "d": 2.50,
            "dp": 1.69,
            "h": 152.00,
            "l": 149.50,
            "o": 149.00,
            "pc": 147.75,
            "t": 1692374400,
        }
    )
    finnhub_client.get_company_profile = AsyncMock(
        return_value={
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "finnhubIndustry": "Technology",
            "country": "US",
            "currency": "USD",
            "ipo": "1980-12-12",
            "marketCapitalization": "3200.12",
            "shareOutstanding": "15600.50",
        }
    )
    finnhub_client.get_basic_financials = AsyncMock(
        return_value={
            "metric": {
                "peTTM": "31.824",
                "pb": "45.12",
                "52WeekPriceReturnDaily": "23.50",
                "beta": "1.234",
                "epsTTM": "6.421",
                "totalDebt/totalEquityQuarterly": "0.42",
            }
        }
    )
    finnhub_client.get_company_news = AsyncMock(
        return_value=[
            {
                "id": 123456,
                "headline": "Apple announces results",
                "source": "Reuters",
                "summary": "Quarterly results released.",
                "url": "https://example.com/news/apple-results",
                "image": "",
                "datetime": 1_724_497_200,
            }
        ]
    )
    return finnhub_client


def await_kwargs(mock: AsyncMock) -> Mapping[str, Any]:
    assert mock.await_args is not None
    return mock.await_args.kwargs


def test_generate_portfolio_explanation_composes_real_services_with_mocked_boundaries(
    client,
    override_dependency,
    session,
    user,
    portfolio,
    security,
) -> None:
    finnhub_client = build_finnhub_client()
    llm_client = MagicMock()
    llm_client.generate_structured = AsyncMock(
        return_value=PortfolioExplanationContent(
            summary="The portfolio is concentrated in AAPL.",
            strengths=[],
            risks=[],
            concentration=[],
            performance=[],
            limitations=[],
        )
    )
    session.add(
        Position(
            portfolio_id=portfolio.id,
            symbol=security.symbol,
            shares=Decimal(10),
            average_cost=Decimal(100),
        )
    )
    session.commit()

    def override_session():
        yield session

    override_dependency(get_session, override_session)
    override_dependency(get_finnhub_client, lambda: finnhub_client)
    override_dependency(get_llm_client, lambda: llm_client)
    override_dependency(
        get_current_user,
        lambda: CurrentUserRead(id=user.id, email=user.email),
    )

    response = client.post(f"/portfolios/{portfolio.id}/explanations")

    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == str(portfolio.id)
    assert body["explanation"]["summary"] == "The portfolio is concentrated in AAPL."
    assert body["data_retrieved_at"]
    assert body["generated_at"]

    request = await_kwargs(llm_client.generate_structured)
    assert request["output_type"] is PortfolioExplanationContent
    assert "portfolio_id" in request["user_prompt"]
    assert "total_market_value" in request["user_prompt"]
    assert "AAPL" in request["user_prompt"]
    assert "allocation_percent" in request["user_prompt"]
    finnhub_client.get_quote.assert_awaited_once_with("AAPL")


def test_generate_security_explanation_composes_real_services_with_mocked_boundaries(
    client,
    override_dependency,
    session,
) -> None:
    finnhub_client = build_finnhub_client()
    llm_client = MagicMock()
    llm_client.generate_structured = AsyncMock(
        return_value=SecurityExplanationContent(
            summary="The security has supplied valuation and fundamentals.",
            valuation=[],
            growth_and_profitability=[],
            financial_health=[],
            performance=[],
            recent_developments=[],
            risks=[],
            limitations=[],
        )
    )

    def override_session():
        yield session

    override_dependency(get_session, override_session)
    override_dependency(get_finnhub_client, lambda: finnhub_client)
    override_dependency(get_llm_client, lambda: llm_client)

    response = client.post("/securities/aapl/explanations")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert (
        body["explanation"]["summary"]
        == "The security has supplied valuation and fundamentals."
    )
    assert body["data_retrieved_at"]
    assert body["generated_at"]

    request = await_kwargs(llm_client.generate_structured)
    assert request["output_type"] is SecurityExplanationContent
    assert "company" in request["user_prompt"]
    assert "quote" in request["user_prompt"]
    assert "valuation" in request["user_prompt"]
    assert "performance" in request["user_prompt"]
    assert "fundamentals" in request["user_prompt"]
    assert "news" in request["user_prompt"]
    finnhub_client.get_quote.assert_awaited_once_with("AAPL")
    finnhub_client.get_company_profile.assert_awaited_once_with("AAPL")
    finnhub_client.get_basic_financials.assert_awaited_once_with("AAPL")
    finnhub_client.get_company_news.assert_awaited_once()
