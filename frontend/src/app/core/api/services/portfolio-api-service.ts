import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { PortfolioAnalyticsRead } from '../models/analytics-model';
import { Uuid } from '../models/api-types';
import { PaginatedResult, PaginationParams } from '../models/pagination-model';
import { PortfolioCreate, PortfolioRead, PortfolioUpdate } from '../models/portfolio-model';

@Injectable({
	providedIn: 'root',
})
export class PortfolioApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	getPortfolios(
		pagination?: PaginationParams,
	): Observable<PaginatedResult<PortfolioRead>> {
		const params = this.getPaginationParams(pagination);

		return this.http.get<PaginatedResult<PortfolioRead>>(
			`${this.baseUrl}/portfolios`,
			{ params },
		);
	}

	getPortfolio(
		portfolioId: Uuid,
	): Observable<PortfolioRead> {
		return this.http.get<PortfolioRead>(
			`${this.baseUrl}/portfolios/${portfolioId}`,
		);
	}

	createPortfolio(
		payload: PortfolioCreate,
	): Observable<PortfolioRead> {
		return this.http.post<PortfolioRead>(
			`${this.baseUrl}/portfolios`,
			payload,
		);
	}

	updatePortfolio(
		portfolioId: Uuid,
		payload: PortfolioUpdate,
	): Observable<PortfolioRead> {
		return this.http.patch<PortfolioRead>(
			`${this.baseUrl}/portfolios/${portfolioId}`,
			payload,
		);
	}

	deletePortfolio(
		portfolioId: Uuid,
	): Observable<void> {
		return this.http.delete<void>(
			`${this.baseUrl}/portfolios/${portfolioId}`,
		);
	}

	getAnalytics(
		portfolioId: Uuid,
	): Observable<PortfolioAnalyticsRead> {
		return this.http.get<PortfolioAnalyticsRead>(
			`${this.baseUrl}/portfolios/${portfolioId}/analytics`,
		);
	}

	private getPaginationParams(
		pagination?: PaginationParams,
	): HttpParams {
		return new HttpParams()
			.set('page', pagination?.page ?? 1)
			.set('page_size', pagination?.pageSize ?? 25);
	}
}
