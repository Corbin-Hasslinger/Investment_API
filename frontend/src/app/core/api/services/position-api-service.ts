import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { Uuid } from '../models/api-types';
import { PaginatedResult, PaginationParams } from '../models/pagination-model';
import { PositionCreate, PositionRead, PositionUpdate } from '../models/position-model';

@Injectable({
	providedIn: 'root',
})
export class PositionApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	getPositions(
		portfolioId: Uuid,
		pagination?: PaginationParams,
	): Observable<PaginatedResult<PositionRead>> {
		const params = this.getPaginationParams(pagination);

		return this.http.get<PaginatedResult<PositionRead>>(
			`${this.baseUrl}/portfolios/${portfolioId}/positions`,
			{ params },
		);
	}

	getPosition(
		portfolioId: Uuid,
		positionId: Uuid,
	): Observable<PositionRead> {
		return this.http.get<PositionRead>(
			`${this.baseUrl}/portfolios/${portfolioId}/positions/${positionId}`,
		);
	}

	createPosition(
		portfolioId: Uuid,
		payload: PositionCreate,
	): Observable<PositionRead> {
		return this.http.post<PositionRead>(
			`${this.baseUrl}/portfolios/${portfolioId}/positions`,
			payload,
		);
	}

	updatePosition(
		portfolioId: Uuid,
		positionId: Uuid,
		payload: PositionUpdate,
	): Observable<PositionRead> {
		return this.http.patch<PositionRead>(
			`${this.baseUrl}/portfolios/${portfolioId}/positions/${positionId}`,
			payload,
		);
	}

	deletePosition(
		portfolioId: Uuid,
		positionId: Uuid,
	): Observable<void> {
		return this.http.delete<void>(
			`${this.baseUrl}/portfolios/${portfolioId}/positions/${positionId}`,
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
