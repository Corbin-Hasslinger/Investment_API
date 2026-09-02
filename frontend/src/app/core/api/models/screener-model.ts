import { DecimalString, IsoDateTime } from './api-types';

export type ScreenerMetric =
	| 'market_cap'
	| 'pe_ratio_ttm'
	| 'price_to_book'
	| 'price_to_sales_ttm'
	| 'price_to_free_cash_flow_ttm'
	| 'revenue_growth_yoy_percent'
	| 'return_on_equity_ttm_percent'
	| 'operating_margin_ttm_percent'
	| 'net_margin_ttm_percent'
	| 'current_ratio'
	| 'debt_to_equity'
	| 'beta'
	| 'return_1_year_percent';

export type ScreenerOperator = 'eq' | 'gt' | 'lt' | 'gte' | 'lte';

export type SortDirection = 'asc' | 'desc';

export interface StockScreenerCriterion {
	metric: ScreenerMetric;
	operator: ScreenerOperator;
	value: DecimalString;
}

export interface StockScreenerRequest {
	criteria: StockScreenerCriterion[];
	sort_by?: ScreenerMetric;
	sort_direction?: SortDirection;
	limit?: number;
	cursor?: string | null;
}

export interface StockScreenerMetricsRead {
	market_cap: DecimalString | null;
	pe_ratio_ttm: DecimalString | null;
	price_to_book: DecimalString | null;
	price_to_sales_ttm: DecimalString | null;
	price_to_free_cash_flow_ttm: DecimalString | null;
	revenue_growth_yoy_percent: DecimalString | null;
	return_on_equity_ttm_percent: DecimalString | null;
	operating_margin_ttm_percent: DecimalString | null;
	net_margin_ttm_percent: DecimalString | null;
	current_ratio: DecimalString | null;
	debt_to_equity: DecimalString | null;
	beta: DecimalString | null;
	return_1_year_percent: DecimalString | null;
}

export interface ScreenerMetricCoverageRead {
	metric: ScreenerMetric;
	in_scope: number;
	evaluable: number;
	missing: number;
}

export interface StockScreenerResultRead {
	symbol: string;
	name: string;
	price: DecimalString | null;
	day_change_percent: DecimalString | null;
	sector: string | null;
	industry: string | null;
	metrics: StockScreenerMetricsRead;
}

export interface StockScreenerRead {
	as_of: IsoDateTime;
	returned_count: number;
	next_cursor: string | null;
	results: StockScreenerResultRead[];
	coverage: ScreenerMetricCoverageRead[];
}
