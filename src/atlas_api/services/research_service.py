import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from atlas_api.clients.finnhub_client import FinnhubClient, JsonValue
from atlas_api.schemas.research import (
    CompanyNewsRead,
    CompanyOverviewRead,
    CompanyResearchRead,
    FundamentalMetricsRead,
    PerformanceMetricsRead,
    ValuationMetricsRead,
)
from atlas_api.services.security_service import SecurityService
from atlas_api.tools.errors import UnsupportedSymbolError, UpstreamUnavailableError

MONEY_PRECISION = Decimal("0.01")
PROFILE_UNIT_MULTIPLIER = Decimal(1000000)


class ResearchService:
    def __init__(
        self, finnhub_client: FinnhubClient, security_service: SecurityService
    ):
        self.finnhub_client = finnhub_client
        self.security_service = security_service

    @staticmethod
    def round_money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_PRECISION)

    @staticmethod
    def _parse_decimal(value: JsonValue) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        if not isinstance(value, (str, int, float, Decimal)):
            return None
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        if not result.is_finite():
            return None
        return result

    @classmethod
    def _to_decimal(cls, value: JsonValue) -> Decimal | None:
        result = cls._parse_decimal(value)
        return cls.round_money(result) if result is not None else None

    @classmethod
    def _to_profile_decimal(cls, value: JsonValue) -> Decimal | None:
        result = cls._parse_decimal(value)
        if result is None:
            return None
        return cls.round_money(result * PROFILE_UNIT_MULTIPLIER)

    @staticmethod
    def _to_optional_string(value: JsonValue) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _to_date(value: JsonValue) -> date | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None

    @staticmethod
    def _to_datetime(value: JsonValue) -> datetime | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if value <= 0:
            return None
        try:
            return datetime.fromtimestamp(value, tz=UTC)
        except (OSError, OverflowError, ValueError):
            return None

    @staticmethod
    def _news_date_range(today: date) -> tuple[date, date]:
        return today - timedelta(days=7), today

    @staticmethod
    def _extract_metrics(
        financials: dict[str, JsonValue],
    ) -> dict[str, JsonValue]:
        """Extracts the 'metric' section from the given financials data."""
        metrics = financials.get("metric")

        if metrics is None:
            return {}
        if not isinstance(metrics, dict):
            raise UpstreamUnavailableError(
                "Finnhub returned an invalid Basic Financials response."
            )
        return metrics

    def _build_company_overview(
        self,
        normalized_symbol: str,
        profile: dict[str, JsonValue],
    ) -> CompanyOverviewRead:
        """Builds a company overview from the given profile data."""
        ticker = self._to_optional_string(profile.get("ticker"))
        name = self._to_optional_string(profile.get("name"))
        if ticker is None or name is None or ticker.upper() != normalized_symbol:
            raise UnsupportedSymbolError(
                f"Symbol '{normalized_symbol}' is not supported by Finnhub."
            )
        return CompanyOverviewRead(
            symbol=normalized_symbol,
            name=name,
            exchange=self._to_optional_string(profile.get("exchange")),
            industry=self._to_optional_string(profile.get("finnhubIndustry")),
            country=self._to_optional_string(profile.get("country")),
            currency=self._to_optional_string(profile.get("currency")),
            ipo_date=self._to_date(profile.get("ipo")),
            website=self._to_optional_string(profile.get("weburl")),
            logo_url=self._to_optional_string(profile.get("logo")),
            market_cap=self._to_profile_decimal(profile.get("marketCapitalization")),
            shares_outstanding=self._to_profile_decimal(
                profile.get("shareOutstanding")
            ),
        )

    def _build_valuation_metrics(
        self, metrics: dict[str, JsonValue]
    ) -> ValuationMetricsRead:
        """Builds valuation metrics for the given symbol."""
        return ValuationMetricsRead(
            pe_ratio_ttm=self._to_decimal(metrics.get("peTTM")),
            price_to_book=self._to_decimal(metrics.get("pb")),
            price_to_sales_ttm=self._to_decimal(metrics.get("psTTM")),
            price_to_free_cash_flow_ttm=self._to_decimal(metrics.get("pfcfShareTTM")),
        )

    def _build_performance_metrics(
        self, metrics: dict[str, JsonValue]
    ) -> PerformanceMetricsRead:
        """Builds performance metrics for the given symbol."""
        return PerformanceMetricsRead(
            fifty_two_week_high=self._to_decimal(metrics.get("52WeekHigh")),
            fifty_two_week_low=self._to_decimal(metrics.get("52WeekLow")),
            beta=self._to_decimal(metrics.get("beta")),
            return_3_month_percent=self._to_decimal(
                metrics.get("13WeekPriceReturnDaily")
            ),
            return_1_year_percent=self._to_decimal(
                metrics.get("52WeekPriceReturnDaily")
            ),
        )

    def _build_fundamental_metrics(
        self, metrics: dict[str, JsonValue]
    ) -> FundamentalMetricsRead:
        """Builds fundamental metrics for the given symbol."""
        return FundamentalMetricsRead(
            eps_ttm=self._to_decimal(metrics.get("epsTTM")),
            revenue_growth_yoy_percent=self._to_decimal(
                metrics.get("revenueGrowthTTMYoy")
            ),
            eps_growth_yoy_percent=self._to_decimal(metrics.get("epsGrowthTTMYoy")),
            gross_margin_percent=self._to_decimal(metrics.get("grossMarginTTM")),
            operating_margin_percent=self._to_decimal(
                metrics.get("operatingMarginTTM")
            ),
            net_margin_percent=self._to_decimal(metrics.get("netProfitMarginTTM")),
            return_on_equity_percent=self._to_decimal(metrics.get("roeTTM")),
            current_ratio=self._to_decimal(metrics.get("currentRatioQuarterly")),
            debt_to_equity=self._to_decimal(
                metrics.get("totalDebt/totalEquityQuarterly")
            ),
        )

    def _build_news(
        self, raw_news: list[dict[str, JsonValue]]
    ) -> list[CompanyNewsRead]:
        """Builds news for the given symbol within the specified date range."""
        articles: list[CompanyNewsRead] = []

        for item in raw_news:
            article_id = item.get("id")
            headline = self._to_optional_string(item.get("headline"))
            source = self._to_optional_string(item.get("source"))
            url = self._to_optional_string(item.get("url"))
            summary = self._to_optional_string(item.get("summary"))
            image_url = self._to_optional_string(item.get("image"))
            published_at = self._to_datetime(item.get("datetime"))

            if (
                isinstance(article_id, bool)
                or not isinstance(article_id, int)
                or headline is None
                or source is None
                or url is None
                or published_at is None
            ):
                continue
            articles.append(
                CompanyNewsRead(
                    id=article_id,
                    headline=headline,
                    source=source,
                    url=url,
                    summary=summary,
                    image_url=image_url,
                    published_at=published_at,
                )
            )
        articles.sort(key=lambda article: article.published_at, reverse=True)
        return articles[:5]

    async def get_company_research(self, symbol: str) -> CompanyResearchRead:
        normalized = self.security_service.normalize_symbol(symbol)
        from_date, to_date = self._news_date_range(datetime.now(UTC).date())

        profile, financial_data, raw_news = await asyncio.gather(
            self.finnhub_client.get_company_profile(normalized),
            self.finnhub_client.get_basic_financials(normalized),
            self.finnhub_client.get_company_news(normalized, from_date, to_date),
        )
        metric_data = self._extract_metrics(financial_data)

        return CompanyResearchRead(
            company=self._build_company_overview(normalized, profile),
            valuation=self._build_valuation_metrics(metric_data),
            performance=self._build_performance_metrics(metric_data),
            fundamentals=self._build_fundamental_metrics(metric_data),
            news=self._build_news(raw_news),
        )
