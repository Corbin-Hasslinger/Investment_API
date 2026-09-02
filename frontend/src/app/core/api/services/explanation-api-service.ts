import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { Uuid } from '../models/api-types';
import { PortfolioExplanationRead, SecurityExplanationRead } from '../models/explanation-model';

@Injectable({
	providedIn: 'root',
})
export class ExplanationApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	explainPortfolio(
		portfolioId: Uuid,
	): Observable<PortfolioExplanationRead> {
		return this.http.post<PortfolioExplanationRead>(
			`${this.baseUrl}/portfolios/${portfolioId}/explanations`,
			null,
		);
	}

	explainSecurity(
		symbol: string,
	): Observable<SecurityExplanationRead> {
		const encodedSymbol = this.getEncodedSymbol(symbol);

		return this.http.post<SecurityExplanationRead>(
			`${this.baseUrl}/securities/${encodedSymbol}/explanations`,
			null,
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
