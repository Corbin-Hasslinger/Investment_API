import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { StockQuote } from '../models/market-model';

@Injectable({
	providedIn: 'root',
})
export class MarketApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	getQuote(
		symbol: string,
	): Observable<StockQuote> {
		const encodedSymbol = this.getEncodedSymbol(symbol);

		return this.http.get<StockQuote>(
			`${this.baseUrl}/market/quote/${encodedSymbol}`,
		);
	}

	private getEncodedSymbol(
		symbol: string,
	): string {
		const normalizedSymbol =
			symbol.trim().toUpperCase();

		return encodeURIComponent(normalizedSymbol);
	}
}
