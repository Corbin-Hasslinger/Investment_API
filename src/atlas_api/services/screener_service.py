from datetime import datetime
from decimal import Decimal, InvalidOperation

from atlas_api.clients.tickerbot_client import JsonObject, TickerbotClient
from atlas_api.schemas.stock import (
    ScreenerMetric,
    ScreenerMetricCoverageRead,
    StockScreenerMetricsRead,
    StockScreenerRead,
    StockScreenerRequest,
    StockScreenerResultRead,
)
from atlas_api.screening.compiler import ScreenerQueryCompiler
from atlas_api.screening.metrics import (
    RATIO_TO_PERCENT,
    SCREENER_METRICS,
    get_metric_definition,
    get_provider_field,
)
from atlas_api.tools.errors import UpstreamResponseError

DEFAULT_PROVIDER_FIELDS = {
    "market_cap",
}
SCREENER_RESULT_COLUMNS = [
    "sector",
    "industry",
    *[
        definition.provider_field
        for definition in SCREENER_METRICS.values()
        if definition.provider_field not in DEFAULT_PROVIDER_FIELDS
    ],
]


class ScreenerService:
    def __init__(
        self, tickerbot_client: TickerbotClient, query_compiler: ScreenerQueryCompiler
    ):
        self.tickerbot_client = tickerbot_client
        self.query_compiler = query_compiler

    def _normalize_decimal(
        self, value: object, scale: Decimal = Decimal(1)
    ) -> Decimal | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise UpstreamResponseError("Tickerbot returned an invalid numeric value.")

        if not isinstance(value, (int, float, str)):
            raise UpstreamResponseError("Tickerbot returned an invalid numeric value.")
        try:
            result = Decimal(str(value)) * scale
        except InvalidOperation as esc:
            raise UpstreamResponseError(
                "Tickerbot returned an invalid numeric value."
            ) from esc
        if not result.is_finite():
            raise UpstreamResponseError("Tickerbot returned an invalid numeric value.")
        return result

    def _metric_value(self, row: JsonObject, metric: ScreenerMetric) -> Decimal | None:
        definition = get_metric_definition(metric)

        raw_value = row.get(definition.provider_field)
        return self._normalize_decimal(raw_value, scale=definition.output_scale)

    def _build_metrics(
        self,
        row: JsonObject,
    ) -> StockScreenerMetricsRead:
        return StockScreenerMetricsRead(
            market_cap=self._metric_value(row, ScreenerMetric.MARKET_CAP),
            pe_ratio_ttm=self._metric_value(row, ScreenerMetric.PE_RATIO_TTM),
            price_to_book=self._metric_value(row, ScreenerMetric.PRICE_TO_BOOK),
            price_to_sales_ttm=self._metric_value(
                row, ScreenerMetric.PRICE_TO_SALES_TTM
            ),
            price_to_free_cash_flow_ttm=self._metric_value(
                row, ScreenerMetric.PRICE_TO_FREE_CASH_FLOW_TTM
            ),
            revenue_growth_yoy_percent=self._metric_value(
                row, ScreenerMetric.REVENUE_GROWTH_YOY_PERCENT
            ),
            return_on_equity_ttm_percent=self._metric_value(
                row, ScreenerMetric.RETURN_ON_EQUITY_TTM_PERCENT
            ),
            operating_margin_ttm_percent=self._metric_value(
                row, ScreenerMetric.OPERATING_MARGIN_TTM_PERCENT
            ),
            net_margin_ttm_percent=self._metric_value(
                row, ScreenerMetric.NET_MARGIN_TTM_PERCENT
            ),
            current_ratio=self._metric_value(row, ScreenerMetric.CURRENT_RATIO),
            debt_to_equity=self._metric_value(row, ScreenerMetric.DEBT_TO_EQUITY),
            beta=self._metric_value(row, ScreenerMetric.BETA),
            return_1_year_percent=self._metric_value(
                row, ScreenerMetric.RETURN_1_YEAR_PERCENT
            ),
        )

    def _require_str(self, row: JsonObject, field: str) -> str:
        value = row.get(field)
        if not isinstance(value, str) or not value:
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid '{field}' value."
            )
        return value

    def _optional_str(self, row: JsonObject, field: str) -> str | None:
        value = row.get(field)
        if value is None:
            return None
        if not isinstance(value, str):
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid '{field}' value."
            )
        return value or None

    def _require_list(self, data: JsonObject, field: str) -> list[JsonObject]:
        value = data.get(field)
        if not isinstance(value, list):
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid '{field}' value."
            )
        items: list[JsonObject] = []
        for item in value:
            if not isinstance(item, dict):
                raise UpstreamResponseError(
                    f"Tickerbot returned an invalid '{field}' value."
                )
            items.append(item)
        return items

    def _require_int(self, data: JsonObject, field: str) -> int:
        value = data.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid '{field}' value."
            )
        return value

    def _require_nonnegative_int(
        self,
        data: JsonObject,
        field: str,
    ) -> int:
        value = self._require_int(data, field)

        if value < 0:
            raise UpstreamResponseError(
                f"Tickerbot returned an invalid '{field}' value."
            )

        return value

    def _parse_as_of(self, provider_response: JsonObject) -> datetime:
        raw_value = self._require_str(provider_response, "as_of")
        try:
            parsed = datetime.fromisoformat(raw_value)
        except ValueError as exc:
            raise UpstreamResponseError(
                "Tickerbot returned an invalid 'as_of' value."
            ) from exc
        if parsed.tzinfo is None:
            raise UpstreamResponseError("Tickerbot returned an invalid 'as_of' value.")
        return parsed

    def _build_coverage(
        self, provider_response: JsonObject, metrics: list[ScreenerMetric]
    ) -> list[ScreenerMetricCoverageRead]:
        meta = provider_response.get("_meta")
        null_coverage = meta.get("null_coverage") if isinstance(meta, dict) else None
        if not isinstance(null_coverage, dict):
            raise UpstreamResponseError(
                "Tickerbot returned an invalid 'null_coverage' value."
            )

        in_scope = self._require_nonnegative_int(null_coverage, "in_scope_rows")
        columns = null_coverage.get("columns")
        if not isinstance(columns, dict):
            raise UpstreamResponseError(
                "Tickerbot returned an invalid 'null_coverage' value."
            )

        coverage: list[ScreenerMetricCoverageRead] = []
        for metric in metrics:
            entry = columns.get(get_provider_field(metric))
            if not isinstance(entry, dict):
                raise UpstreamResponseError(
                    "Tickerbot returned incomplete metric coverage."
                )
            evaluable = self._require_nonnegative_int(entry, "evaluable_rows")
            missing = self._require_nonnegative_int(entry, "null_rows")
            if evaluable + missing != in_scope:
                raise UpstreamResponseError(
                    "Tickerbot returned inconsistent metric coverage."
                )
            coverage.append(
                ScreenerMetricCoverageRead(
                    metric=metric,
                    in_scope=in_scope,
                    evaluable=evaluable,
                    missing=missing,
                )
            )
        return coverage

    def _build_result(self, row: JsonObject) -> StockScreenerResultRead:
        return StockScreenerResultRead(
            symbol=self._require_str(row, "ticker"),
            name=self._require_str(row, "name"),
            price=self._normalize_decimal(row.get("price")),
            day_change_percent=self._normalize_decimal(
                row.get("day_change_pct"), scale=RATIO_TO_PERCENT
            ),
            sector=self._optional_str(row, "sector"),
            industry=self._optional_str(row, "industry"),
            metrics=self._build_metrics(row),
        )

    async def screen_stocks(self, request: StockScreenerRequest) -> StockScreenerRead:
        query = self.query_compiler.compile(request.criteria)

        provider_order = get_provider_field(request.sort_by)

        provider_response = await self.tickerbot_client.scan(
            query=query,
            order=provider_order,
            direction=request.sort_direction.value,
            limit=request.limit,
            columns=SCREENER_RESULT_COLUMNS,
            cursor=request.cursor,
        )
        rows = self._require_list(provider_response, "results")
        results = [self._build_result(row) for row in rows]
        returned_count = len(results)
        next_cursor = provider_response.get("next_cursor")
        if next_cursor is not None and not isinstance(next_cursor, str):
            raise UpstreamResponseError(
                "Tickerbot returned an invalid 'next_cursor' value."
            )

        requested_metrics = list(
            dict.fromkeys(criterion.metric for criterion in request.criteria)
        )
        coverage = self._build_coverage(provider_response, requested_metrics)

        return StockScreenerRead(
            as_of=self._parse_as_of(provider_response),
            returned_count=returned_count,
            next_cursor=next_cursor,
            results=results,
            coverage=coverage,
        )
