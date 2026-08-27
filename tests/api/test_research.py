from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_api.di import get_research_service
from atlas_api.schemas.research import (
    CompanyNewsRead,
    CompanyOverviewRead,
    CompanyResearchRead,
    FundamentalMetricsRead,
    PerformanceMetricsRead,
    ValuationMetricsRead,
)
from atlas_api.services.research_service import ResearchService
from atlas_api.tools.errors import (
    InvalidSymbolFormatError,
    UnsupportedSymbolError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)


def build_company_research_read() -> CompanyResearchRead:
    return CompanyResearchRead(
        company=CompanyOverviewRead(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            industry="Technology",
            country="US",
            currency="USD",
            ipo_date=date(1980, 12, 12),
            website="https://www.apple.com",
            logo_url="https://logo.clearbit.com/apple.com",
            market_cap=Decimal("3200120000.00"),
            shares_outstanding=Decimal("15600500000.00"),
        ),
        valuation=ValuationMetricsRead(
            pe_ratio_ttm=Decimal("31.82"),
            price_to_book=Decimal("44.10"),
            price_to_sales_ttm=Decimal("8.21"),
            price_to_free_cash_flow_ttm=Decimal("29.35"),
        ),
        performance=PerformanceMetricsRead(
            fifty_two_week_high=Decimal("237.49"),
            fifty_two_week_low=Decimal("164.08"),
            beta=Decimal("1.23"),
            return_3_month_percent=Decimal("4.57"),
            return_1_year_percent=Decimal("18.11"),
        ),
        fundamentals=FundamentalMetricsRead(
            eps_ttm=Decimal("6.42"),
            revenue_growth_yoy_percent=Decimal("4.20"),
            eps_growth_yoy_percent=Decimal("7.11"),
            gross_margin_percent=Decimal("45.50"),
            operating_margin_percent=Decimal("30.20"),
            net_margin_percent=Decimal("24.11"),
            return_on_equity_percent=Decimal("160.20"),
            current_ratio=Decimal("0.99"),
            debt_to_equity=Decimal("1.55"),
        ),
        news=[
            CompanyNewsRead(
                id=123456,
                headline="Apple announces results",
                source="Reuters",
                summary="Quarterly results released.",
                url="https://example.com/news/apple-results",
                image_url="https://example.com/news/apple-results.jpg",
                published_at=datetime(2026, 8, 24, 15, 30, tzinfo=UTC),
            )
        ],
    )


def build_minimal_company_research_read() -> CompanyResearchRead:
    return CompanyResearchRead(
        company=CompanyOverviewRead(symbol="AAPL", name="Apple Inc."),
        valuation=ValuationMetricsRead(),
        performance=PerformanceMetricsRead(),
        fundamentals=FundamentalMetricsRead(),
        news=[],
    )


def override_research_service(override_dependency) -> MagicMock:
    service = MagicMock(spec=ResearchService)
    service.get_company_research = AsyncMock()
    override_dependency(get_research_service, lambda: service)
    return service


def test_get_company_research_returns_200_with_complete_response(
    client, override_dependency
) -> None:
    research_service = override_research_service(override_dependency)
    research = build_company_research_read()
    research_service.get_company_research.return_value = research

    response = client.get("/research/company/AAPL")

    assert response.status_code == 200
    body = response.json()
    assert body["company"]["symbol"] == "AAPL"
    assert body["company"]["name"] == "Apple Inc."
    assert body["company"]["ipo_date"] == "1980-12-12"
    assert body["valuation"]["pe_ratio_ttm"] == "31.82"
    assert body["performance"]["beta"] == "1.23"
    assert body["fundamentals"]["eps_ttm"] == "6.42"
    assert body["news"][0]["id"] == 123456
    assert body["news"][0]["published_at"].endswith("Z")
    assert isinstance(body["news"], list)
    research_service.get_company_research.assert_awaited_once_with("AAPL")


def test_get_company_research_returns_200_with_minimal_partial_response(
    client, override_dependency
) -> None:
    research_service = override_research_service(override_dependency)
    research_service.get_company_research.return_value = (
        build_minimal_company_research_read()
    )

    response = client.get("/research/company/AAPL")

    assert response.status_code == 200
    body = response.json()
    assert body["company"]["symbol"] == "AAPL"
    assert body["company"]["name"] == "Apple Inc."
    assert body["valuation"] is not None
    assert body["performance"] is not None
    assert body["fundamentals"] is not None
    assert body["valuation"]["pe_ratio_ttm"] is None
    assert body["performance"]["beta"] is None
    assert body["fundamentals"]["eps_ttm"] is None
    assert body["news"] == []
    research_service.get_company_research.assert_awaited_once_with("AAPL")


def test_get_company_research_returns_400_for_invalid_symbol(
    client, override_dependency
) -> None:
    research_service = override_research_service(override_dependency)
    research_service.get_company_research.side_effect = InvalidSymbolFormatError(
        "Invalid symbol format"
    )

    response = client.get("/research/company/INVALID$")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_symbol_format"
    research_service.get_company_research.assert_awaited_once_with("INVALID$")


def test_get_company_research_returns_400_for_unsupported_symbol(
    client, override_dependency
) -> None:
    research_service = override_research_service(override_dependency)
    research_service.get_company_research.side_effect = UnsupportedSymbolError(
        "Symbol 'FAKEZZ' is not supported by Finnhub."
    )

    response = client.get("/research/company/FAKEZZ")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_symbol"
    research_service.get_company_research.assert_awaited_once_with("FAKEZZ")


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (
            UpstreamRateLimitedError("Finnhub rate limited"),
            429,
            "upstream_rate_limited",
        ),
        (UpstreamUnavailableError("Finnhub unavailable"), 503, "upstream_unavailable"),
        (UpstreamTimeoutError("Finnhub timed out"), 504, "upstream_timeout"),
    ],
)
def test_get_company_research_maps_upstream_failures(
    client,
    override_dependency,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    research_service = override_research_service(override_dependency)
    research_service.get_company_research.side_effect = error

    response = client.get("/research/company/AAPL")

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    research_service.get_company_research.assert_awaited_once_with("AAPL")
