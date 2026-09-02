import { DecimalString } from './api-types';

export interface StockQuote {
	symbol: string;
	current_price: DecimalString;
	price_change: DecimalString;
	percent_change: DecimalString;
	high_price: DecimalString;
	low_price: DecimalString;
	open_price: DecimalString;
	previous_close_price: DecimalString;
	timestamp: number;
}
