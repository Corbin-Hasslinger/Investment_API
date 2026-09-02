import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { StockScreenerRead, StockScreenerRequest } from '../models/screener-model';

@Injectable({
	providedIn: 'root',
})
export class ScreenerApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	screenStocks(
		request: StockScreenerRequest,
	): Observable<StockScreenerRead> {
		return this.http.post<StockScreenerRead>(
			`${this.baseUrl}/screeners/stocks`,
			request,
		);
	}
}
