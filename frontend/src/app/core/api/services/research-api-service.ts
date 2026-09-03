import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../api-base-url';
import { CompanyResearchRead } from '../models/research-model';
import { encodeSymbol } from '../symbol';

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
		const encodedSymbol = encodeSymbol(symbol);

		return this.http.get<CompanyResearchRead>(
			`${this.baseUrl}/research/company/${encodedSymbol}`,
		);
	}
}
