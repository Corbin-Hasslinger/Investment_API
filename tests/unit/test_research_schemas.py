from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, cast

import pytest
from pydantic import ValidationError

from atlas_api.schemas.research import (
    CompanyNewsRead,
    CompanyOverviewRead,
    CompanyResearchRead,
    FundamentalMetricsRead,
    PerformanceMetricsRead,
    ValuationMetricsRead,
)


def build_complete_payload() -> dict[str, Any]:
    return {
        "company": {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "industry": "Consumer Electronics",
            "country": "US",
            "currency": "USD",
            "ipo_date": "1980-12-12",
            "website": "https://www.apple.com",
            "logo_url": "https://logo.clearbit.com/apple.com",
            "market_cap": "3200000000000.00",
            "shares_outstanding": "15600000000.00",
        },
        "valuation": {
            "pe_ratio_ttm": "31.82",
            "price_to_book": "44.10",
            "price_to_sales_ttm": "8.20",
            "price_to_free_cash_flow_ttm": "29.35",
        },
        "performance": {
            "fifty_two_week_high": "220.00",
            "fifty_two_week_low": "164.00",
            "beta": "1.05",
            "return_3_month_percent": "5.75",
            "return_1_year_percent": "18.10",
        },
        "fundamentals": {
            "eps_ttm": "6.42",
            "revenue_growth_yoy_percent": "4.20",
            "eps_growth_yoy_percent": "7.10",
            "gross_margin_percent": "45.50",
            "operating_margin_percent": "30.20",
            "net_margin_percent": "24.10",
            "return_on_equity_percent": "160.20",
            "current_ratio": "0.99",
            "debt_to_equity": "1.55",
        },
        "news": [
            {
                "id": 12345678,
                "headline": "Apple announces new product line",
                "source": "Reuters",
                "summary": "Apple introduced new devices during keynote.",
                "url": "https://example.com/news/apple-product",
                "image_url": "https://example.com/news/apple-product.jpg",
                "published_at": "2026-08-23T14:30:00Z",
            }
        ],
    }


class TestCompanyResearchSchema:
    def test_complete_research_response(self):
        model = CompanyResearchRead.model_validate(build_complete_payload())

        assert isinstance(model.company, CompanyOverviewRead)
        assert isinstance(model.valuation, ValuationMetricsRead)
        assert isinstance(model.performance, PerformanceMetricsRead)
        assert isinstance(model.fundamentals, FundamentalMetricsRead)
        assert isinstance(model.news, list)
        assert len(model.news) == 1
        assert isinstance(model.news[0], CompanyNewsRead)

        assert isinstance(model.company.market_cap, Decimal)
        assert isinstance(model.valuation.pe_ratio_ttm, Decimal)
        assert isinstance(model.performance.beta, Decimal)
        assert isinstance(model.fundamentals.eps_ttm, Decimal)

        assert isinstance(model.company.ipo_date, date)
        assert model.news[0].published_at.tzinfo is not None

    def test_minimal_valid_response(self):
        payload = {
            "company": {"symbol": "AAPL", "name": "Apple Inc."},
            "valuation": {},
            "performance": {},
            "fundamentals": {},
            "news": [],
        }

        model = CompanyResearchRead.model_validate(payload)

        assert model.company.symbol == "AAPL"
        assert model.company.name == "Apple Inc."
        assert model.company.exchange is None
        assert model.company.industry is None
        assert model.company.country is None
        assert model.company.currency is None
        assert model.company.ipo_date is None
        assert model.company.website is None
        assert model.company.logo_url is None
        assert model.company.market_cap is None
        assert model.company.shares_outstanding is None

        assert model.valuation.pe_ratio_ttm is None
        assert model.valuation.price_to_book is None
        assert model.valuation.price_to_sales_ttm is None
        assert model.valuation.price_to_free_cash_flow_ttm is None
        assert model.performance.beta is None
        assert model.performance.return_1_year_percent is None
        assert model.fundamentals.eps_ttm is None
        assert model.fundamentals.debt_to_equity is None
        assert model.news == []

    @pytest.mark.parametrize("missing_field", ["symbol", "name"])
    def test_required_company_identity(self, missing_field: str):
        payload = build_complete_payload()
        company = dict(cast(dict[str, Any], payload["company"]))
        company.pop(missing_field)
        payload["company"] = company

        with pytest.raises(ValidationError):
            CompanyResearchRead.model_validate(payload)

    @pytest.mark.parametrize(
        "missing_section",
        ["company", "valuation", "performance", "fundamentals", "news"],
    )
    def test_required_top_level_sections(self, missing_section: str):
        payload = build_complete_payload()
        payload.pop(missing_section)

        with pytest.raises(ValidationError):
            CompanyResearchRead.model_validate(payload)

    @pytest.mark.parametrize(
        "payload_mutation",
        [
            lambda payload: payload.update({"unknown": "x"}),
            lambda payload: payload["company"].update({"unknown_company": "x"}),
            lambda payload: payload["valuation"].update({"unknown_metric": "x"}),
            lambda payload: payload["news"][0].update({"unknown_news": "x"}),
        ],
    )
    def test_extra_fields_are_forbidden(self, payload_mutation):
        payload = build_complete_payload()
        payload_mutation(payload)

        with pytest.raises(ValidationError):
            CompanyResearchRead.model_validate(payload)

    def test_decimal_json_serialization(self):
        payload = build_complete_payload()
        valuation = cast(dict[str, Any], payload["valuation"])
        performance = cast(dict[str, Any], payload["performance"])
        fundamentals = cast(dict[str, Any], payload["fundamentals"])
        valuation["pe_ratio_ttm"] = Decimal("31.82")
        performance["return_3_month_percent"] = Decimal(0)
        fundamentals["net_margin_percent"] = Decimal("-4.25")
        model = CompanyResearchRead.model_validate(payload)

        dumped = model.model_dump(mode="json")

        assert dumped["valuation"]["pe_ratio_ttm"] == "31.82"
        assert dumped["performance"]["return_3_month_percent"] == "0"
        assert dumped["fundamentals"]["net_margin_percent"] == "-4.25"

    def test_ipo_date_serialization(self):
        model = CompanyResearchRead.model_validate(build_complete_payload())

        dumped = model.model_dump(mode="json")

        assert dumped["company"]["ipo_date"] == "1980-12-12"

    def test_aware_publication_timestamp_requirements(self):
        aware_news = CompanyNewsRead.model_validate(
            {
                "id": 12345678,
                "headline": "Headline",
                "source": "Source",
                "summary": None,
                "url": "https://example.com/news",
                "image_url": None,
                "published_at": datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
            }
        )
        aware_dumped = aware_news.model_dump(mode="json")

        assert aware_news.published_at.tzinfo is not None
        assert aware_dumped["published_at"].endswith("Z")

        with pytest.raises(ValidationError):
            CompanyNewsRead.model_validate(
                {
                    "id": 12345678,
                    "headline": "Headline",
                    "source": "Source",
                    "summary": None,
                    "url": "https://example.com/news",
                    "image_url": None,
                    "published_at": "2026-08-23T12:00:00",
                }
            )

    def test_empty_news_list_is_valid(self):
        payload = build_complete_payload()
        payload["news"] = []

        model = CompanyResearchRead.model_validate(payload)
        dumped = model.model_dump(mode="json")

        assert model.news == []
        assert dumped["news"] == []

    def test_partial_metrics(self):
        payload = {
            "company": {"symbol": "AAPL", "name": "Apple Inc."},
            "valuation": {"pe_ratio_ttm": "31.82"},
            "performance": {"beta": "1.05"},
            "fundamentals": {"eps_ttm": "6.42"},
            "news": [],
        }

        model = CompanyResearchRead.model_validate(payload)

        assert model.valuation.pe_ratio_ttm == Decimal("31.82")
        assert model.performance.beta == Decimal("1.05")
        assert model.fundamentals.eps_ttm == Decimal("6.42")

        assert model.valuation.price_to_book is None
        assert model.valuation.price_to_sales_ttm is None
        assert model.performance.fifty_two_week_high is None
        assert model.fundamentals.revenue_growth_yoy_percent is None
        assert model.fundamentals.net_margin_percent is None

        assert isinstance(model, CompanyResearchRead)
