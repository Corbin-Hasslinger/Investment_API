import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { CompanyResearchRead } from '../models/research-model';

@Injectable({
	providedIn: 'root',
})
export class ResearchApiService {
	private readonly http =
		inject(HttpClient);

	private readonly baseUrl =
		inject(API_BASE_URL);

	getCompanyResearch(
		symbol: string,
	): Observable<CompanyResearchRead> {
		const encodedSymbol = this.getEncodedSymbol(symbol);

		return this.http.get<CompanyResearchRead>(
			`${this.baseUrl}/research/company/${encodedSymbol}`,
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
