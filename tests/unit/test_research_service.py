import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, date
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_api.clients.finnhub_client import FinnhubClient, JsonObject
from atlas_api.schemas.research import CompanyResearchRead
from atlas_api.services.research_service import ResearchService
from atlas_api.services.security_service import SecurityService
from atlas_api.tools.errors import (
	UnsupportedSymbolError,
	UpstreamRateLimitedError,
	UpstreamTimeoutError,
	UpstreamUnavailableError,
)


@pytest.fixture
def finnhub_client() -> MagicMock:
	client = MagicMock(spec=FinnhubClient)
	client.get_company_profile = AsyncMock()
	client.get_basic_financials = AsyncMock()
	client.get_company_news = AsyncMock()
	return client


@pytest.fixture
def security_service() -> MagicMock:
	service = MagicMock(spec=SecurityService)
	service.normalize_symbol.return_value = "AAPL"
	return service


@pytest.fixture
def research_service(
	finnhub_client: MagicMock,
	security_service: MagicMock,
) -> ResearchService:
	return ResearchService(
		finnhub_client=finnhub_client,
		security_service=security_service,
	)


@pytest.fixture
def fixed_news_dates(monkeypatch) -> tuple[date, date]:
	from_date = date(2026, 8, 18)
	to_date = date(2026, 8, 25)
	monkeypatch.setattr(
		ResearchService,
		"_news_date_range",
		staticmethod(lambda today: (from_date, to_date)),
	)
	return from_date, to_date


@pytest.fixture
def aapl_profile() -> JsonObject:
	return {
		"ticker": "AAPL",
		"name": "Apple Inc.",
		"exchange": "NASDAQ",
		"finnhubIndustry": "Technology",
		"country": "US",
		"currency": "USD",
		"ipo": "1980-12-12",
		"weburl": "https://www.apple.com",
		"logo": "https://logo.clearbit.com/apple.com",
		"marketCapitalization": "3200.12",
		"shareOutstanding": "15600.50001953125",
	}


@pytest.fixture
def aapl_basic_financials() -> JsonObject:
	return {
		"metric": {
			"peTTM": "31.824",
			"pb": "44.104",
			"psTTM": "8.206",
			"pfcfShareTTM": "29.354",
			"52WeekHigh": "237.49",
			"52WeekLow": "164.08",
			"beta": "1.234",
			"13WeekPriceReturnDaily": "4.567",
			"52WeekPriceReturnDaily": "18.109",
			"epsTTM": "6.421",
			"revenueGrowthTTMYoy": "4.205",
			"epsGrowthTTMYoy": "7.106",
			"grossMarginTTM": "45.504",
			"operatingMarginTTM": "30.205",
			"netProfitMarginTTM": "24.106",
			"roeTTM": "160.204",
			"currentRatioQuarterly": "0.994",
			"totalDebt/totalEquityQuarterly": "1.554",
		}
	}


@pytest.fixture
def partial_jpm_basic_financials() -> JsonObject:
	return {
		"metric": {
			"peTTM": "12.34",
			"52WeekHigh": "225.50",
			"epsTTM": "18.25",
			"netProfitMarginTTM": "28.40",
		}
	}


@pytest.fixture
def more_than_five_news_articles() -> list[JsonObject]:
	return [
		{
			"id": index,
			"headline": f"Apple headline {index}",
			"source": "Reuters",
			"summary": "Summary",
			"url": f"https://example.com/news/{index}",
			"image": f"https://example.com/news/{index}.jpg",
			"datetime": 1_700_000_000 + index,
		}
		for index in range(1, 8)
	]


@pytest.fixture
def empty_news_list() -> list[JsonObject]:
	return []


@pytest.fixture
def malformed_news_record() -> JsonObject:
	return {
		"id": 999,
		"headline": "",
		"source": "Reuters",
		"url": "https://example.com/news/malformed",
		"datetime": 1_700_000_000,
	}


def configure_upstream(
	finnhub_client: MagicMock,
	profile: Mapping[str, object],
	financials: Mapping[str, object],
	news: Sequence[Mapping[str, object]],
) -> None:
	finnhub_client.get_company_profile.return_value = profile
	finnhub_client.get_basic_financials.return_value = financials
	finnhub_client.get_company_news.return_value = news


def assert_only_normalize_used(security_service: MagicMock) -> None:
	security_service.normalize_symbol.assert_called()
	security_service.resolve_security.assert_not_called()


@pytest.mark.asyncio
async def test_get_company_research_returns_complete_response(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	security_service: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	aapl_basic_financials: dict[str, object],
	more_than_five_news_articles: list[dict[str, object]],
) -> None:
	configure_upstream(
		finnhub_client,
		aapl_profile,
		aapl_basic_financials,
		more_than_five_news_articles,
	)

	result = await research_service.get_company_research(" aapl ")

	assert isinstance(result, CompanyResearchRead)
	assert result.company.symbol == "AAPL"
	assert result.company.name == "Apple Inc."
	assert result.company.exchange == "NASDAQ"
	assert result.company.industry == "Technology"
	assert result.company.market_cap == Decimal("3200120000.00")
	assert result.company.shares_outstanding == Decimal("15600500019.53")
	assert result.valuation.pe_ratio_ttm == Decimal("31.82")
	assert result.valuation.price_to_book == Decimal("44.10")
	assert result.valuation.price_to_sales_ttm == Decimal("8.21")
	assert result.performance.beta == Decimal("1.23")
	assert result.performance.return_3_month_percent == Decimal("4.57")
	assert result.fundamentals.eps_ttm == Decimal("6.42")
	assert result.fundamentals.gross_margin_percent == Decimal("45.50")
	assert result.fundamentals.current_ratio == Decimal("0.99")
	assert len(result.news) == 5
	assert [article.id for article in result.news] == [7, 6, 5, 4, 3]
	assert all(article.published_at.tzinfo is not None for article in result.news)
	assert all(article.published_at.tzinfo == UTC for article in result.news)
	assert_only_normalize_used(security_service)


@pytest.mark.asyncio
async def test_get_company_research_normalizes_and_calls_upstream_once_each(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	security_service: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	aapl_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
) -> None:
	from_date, to_date = fixed_news_dates
	security_service.normalize_symbol.return_value = "AAPL"
	configure_upstream(finnhub_client, aapl_profile, aapl_basic_financials, empty_news_list)

	await research_service.get_company_research(" aapl ")

	security_service.normalize_symbol.assert_called_once_with(" aapl ")
	finnhub_client.get_company_profile.assert_awaited_once_with("AAPL")
	finnhub_client.get_basic_financials.assert_awaited_once_with("AAPL")
	finnhub_client.get_company_news.assert_awaited_once_with("AAPL", from_date, to_date)
	assert finnhub_client.get_basic_financials.await_count == 1
	assert_only_normalize_used(security_service)


def test_news_date_range_is_deterministic() -> None:
	from_date, to_date = ResearchService._news_date_range(date(2026, 8, 25))

	assert from_date == date(2026, 8, 18)
	assert to_date == date(2026, 8, 25)


@pytest.mark.asyncio
async def test_get_company_research_allows_partial_financial_data(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	security_service: MagicMock,
	fixed_news_dates: tuple[date, date],
	partial_jpm_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
) -> None:
	security_service.normalize_symbol.return_value = "JPM"
	profile = {"ticker": "JPM", "name": "JPMorgan Chase & Co."}
	configure_upstream(finnhub_client, profile, partial_jpm_basic_financials, empty_news_list)

	result = await research_service.get_company_research("jpm")

	assert isinstance(result, CompanyResearchRead)
	assert result.company.symbol == "JPM"
	assert result.valuation.pe_ratio_ttm == Decimal("12.34")
	assert result.performance.fifty_two_week_high == Decimal("225.50")
	assert result.fundamentals.eps_ttm == Decimal("18.25")
	assert result.fundamentals.net_margin_percent == Decimal("28.40")
	assert result.fundamentals.gross_margin_percent is None
	assert result.fundamentals.current_ratio is None
	assert result.valuation is not None
	assert result.performance is not None
	assert result.fundamentals is not None
	assert_only_normalize_used(security_service)


@pytest.mark.asyncio
@pytest.mark.parametrize("financials", [{}, {"metric": None}])
async def test_get_company_research_treats_missing_metric_envelope_as_empty_metrics(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	empty_news_list: list[dict[str, object]],
	financials: dict[str, object],
) -> None:
	configure_upstream(finnhub_client, aapl_profile, financials, empty_news_list)

	result = await research_service.get_company_research("AAPL")

	assert all(value is None for value in result.valuation.model_dump().values())
	assert all(value is None for value in result.performance.model_dump().values())
	assert all(value is None for value in result.fundamentals.model_dump().values())


@pytest.mark.asyncio
async def test_get_company_research_rejects_invalid_metric_envelope(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	empty_news_list: list[dict[str, object]],
) -> None:
	configure_upstream(finnhub_client, aapl_profile, {"metric": []}, empty_news_list)

	with pytest.raises(UpstreamUnavailableError):
		await research_service.get_company_research("AAPL")


@pytest.mark.asyncio
@pytest.mark.parametrize(
	"profile",
	[
		{},
		{"name": "Apple Inc."},
		{"ticker": "", "name": "Apple Inc."},
		{"ticker": "AAPL"},
		{"ticker": "AAPL", "name": ""},
		{"ticker": "MSFT", "name": "Microsoft Corporation"},
	],
)
async def test_get_company_research_rejects_unsupported_company_identity(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
	profile: dict[str, object],
) -> None:
	configure_upstream(finnhub_client, profile, aapl_basic_financials, empty_news_list)

	with pytest.raises(UnsupportedSymbolError):
		await research_service.get_company_research("AAPL")


def test_build_news_returns_empty_list_for_no_news(
	research_service: ResearchService,
	empty_news_list: list[dict[str, object]],
) -> None:
	assert research_service._build_news(cast(list[JsonObject], empty_news_list)) == []


def test_build_news_sorts_newest_first_and_limits_to_five(
	research_service: ResearchService,
	more_than_five_news_articles: list[dict[str, object]],
) -> None:
	result = research_service._build_news(
		cast(list[JsonObject], more_than_five_news_articles)
	)

	assert len(result) == 5
	assert [article.id for article in result] == [7, 6, 5, 4, 3]
	assert [article.published_at for article in result] == sorted(
		[article.published_at for article in result],
		reverse=True,
	)


def test_build_news_normalizes_empty_summary_and_image(
	research_service: ResearchService,
) -> None:
	result = research_service._build_news(
		[
			{
				"id": 1,
				"headline": "Headline",
				"source": "Reuters",
				"summary": "   ",
				"url": "https://example.com/news/1",
				"image": "",
				"datetime": 1_700_000_000,
			}
		]
	)

	assert len(result) == 1
	assert result[0].summary is None
	assert result[0].image_url is None


def test_build_news_skips_one_malformed_article(
	research_service: ResearchService,
	malformed_news_record: dict[str, object],
) -> None:
	valid = {
		"id": 1,
		"headline": "Headline",
		"source": "Reuters",
		"url": "https://example.com/news/1",
		"datetime": 1_700_000_000,
	}

	result = research_service._build_news(
		cast(list[JsonObject], [malformed_news_record, valid])
	)

	assert [article.id for article in result] == [1]


@pytest.mark.parametrize(
	"raw_news",
	[
		[
			{
				"id": True,
				"headline": "Headline",
				"source": "Reuters",
				"url": "https://example.com/news/bool-id",
				"datetime": 1_700_000_000,
			}
		],
		[
			{
				"id": 1,
				"headline": "Headline",
				"source": "Reuters",
				"url": "https://example.com/news/bad-time",
				"datetime": "not-a-timestamp",
			}
		],
		[
			{
				"id": 1,
				"headline": "",
				"source": "Reuters",
				"url": "https://example.com/news/missing-headline",
				"datetime": 1_700_000_000,
			}
		],
	],
)
def test_build_news_returns_empty_when_all_articles_are_malformed(
	research_service: ResearchService,
	raw_news: list[JsonObject],
) -> None:
	assert research_service._build_news(raw_news) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
	("method_name", "error"),
	[
		("get_company_profile", UpstreamTimeoutError("profile timeout")),
		("get_basic_financials", UpstreamRateLimitedError("financials rate limited")),
		("get_company_news", UpstreamUnavailableError("news unavailable")),
	],
)
async def test_get_company_research_propagates_upstream_errors(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	aapl_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
	method_name: str,
	error: Exception,
) -> None:
	configure_upstream(finnhub_client, aapl_profile, aapl_basic_financials, empty_news_list)
	getattr(finnhub_client, method_name).side_effect = error

	with pytest.raises(type(error)):
		await research_service.get_company_research("AAPL")


@pytest.mark.asyncio
async def test_get_company_research_starts_upstream_calls_concurrently(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	aapl_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
) -> None:
	started: set[str] = set()
	all_started = asyncio.Event()

	async def wait_for_all_started(name: str, value):
		started.add(name)
		if len(started) == 3:
			all_started.set()
		await all_started.wait()
		return value

	async def get_company_profile(symbol: str):
		return await wait_for_all_started("profile", aapl_profile)

	async def get_basic_financials(symbol: str):
		return await wait_for_all_started("financials", aapl_basic_financials)

	async def get_company_news(symbol: str, from_date: date, to_date: date):
		return await wait_for_all_started("news", empty_news_list)

	finnhub_client.get_company_profile.side_effect = get_company_profile
	finnhub_client.get_basic_financials.side_effect = get_basic_financials
	finnhub_client.get_company_news.side_effect = get_company_news

	result = await asyncio.wait_for(
		research_service.get_company_research("AAPL"),
		timeout=1,
	)

	assert isinstance(result, CompanyResearchRead)
	assert started == {"profile", "financials", "news"}


@pytest.mark.asyncio
async def test_get_company_research_does_not_resolve_or_write_security(
	research_service: ResearchService,
	finnhub_client: MagicMock,
	security_service: MagicMock,
	fixed_news_dates: tuple[date, date],
	aapl_profile: dict[str, object],
	aapl_basic_financials: dict[str, object],
	empty_news_list: list[dict[str, object]],
) -> None:
	configure_upstream(finnhub_client, aapl_profile, aapl_basic_financials, empty_news_list)

	await research_service.get_company_research("AAPL")

	security_service.normalize_symbol.assert_called_once_with("AAPL")
	security_service.resolve_security.assert_not_called()
