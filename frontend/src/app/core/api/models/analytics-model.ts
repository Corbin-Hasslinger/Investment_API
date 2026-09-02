import { DecimalString, Uuid } from './api-types';

export interface PortfolioPositionAnalyticsRead {
	symbol: string;
	shares: DecimalString;
	average_cost: DecimalString;
	current_price: DecimalString;
	market_value: DecimalString;
	cost_basis: DecimalString;
	unrealized_gain_loss: DecimalString;
	unrealized_gain_loss_percent: DecimalString | null;
	allocation_percent: DecimalString;
}

export interface PortfolioAnalyticsRead {
	portfolio_id: Uuid;
	total_market_value: DecimalString;
	total_cost_basis: DecimalString;
	total_unrealized_gain_loss: DecimalString;
	total_unrealized_gain_loss_percent: DecimalString | null;
	positions: PortfolioPositionAnalyticsRead[];
}
