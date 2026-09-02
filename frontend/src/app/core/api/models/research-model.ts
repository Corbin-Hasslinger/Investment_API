import { DecimalString, IsoDate, IsoDateTime } from './api-types';

export interface CompanyOverviewRead {
	symbol: string;
	name: string;
	exchange: string | null;
	industry: string | null;
	country: string | null;
	currency: string | null;
	ipo_date: IsoDate | null;
	website: string | null;
	logo_url: string | null;
	market_cap: DecimalString | null;
	shares_outstanding: DecimalString | null;
}

export interface ValuationMetricsRead {
	pe_ratio_ttm: DecimalString | null;
	price_to_book: DecimalString | null;
	price_to_sales_ttm: DecimalString | null;
	price_to_free_cash_flow_ttm: DecimalString | null;
}

export interface PerformanceMetricsRead {
	fifty_two_week_high: DecimalString | null;
	fifty_two_week_low: DecimalString | null;
	beta: DecimalString | null;
	return_3_month_percent: DecimalString | null;
	return_1_year_percent: DecimalString | null;
}

export interface FundamentalMetricsRead {
	eps_ttm: DecimalString | null;
	revenue_growth_yoy_percent: DecimalString | null;
	eps_growth_yoy_percent: DecimalString | null;
	gross_margin_percent: DecimalString | null;
	operating_margin_percent: DecimalString | null;
	net_margin_percent: DecimalString | null;
	return_on_equity_percent: DecimalString | null;
	current_ratio: DecimalString | null;
	debt_to_equity: DecimalString | null;
}

export interface CompanyNewsRead {
	id: number;
	headline: string;
	source: string;
	summary: string | null;
	url: string;
	image_url: string | null;
	published_at: IsoDateTime;
}

export interface CompanyResearchRead {
	company: CompanyOverviewRead;
	valuation: ValuationMetricsRead;
	performance: PerformanceMetricsRead;
	fundamentals: FundamentalMetricsRead;
	news: CompanyNewsRead[];
}
