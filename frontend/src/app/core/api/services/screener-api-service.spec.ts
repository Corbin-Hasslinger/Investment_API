import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { StockScreenerRead, StockScreenerRequest } from '../models/screener-model';
import { ScreenerApiService } from './screener-api-service';

describe('ScreenerApiService', () => {
  const baseUrl = 'https://api.test';
  let service: ScreenerApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(ScreenerApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('posts the screener body exactly and preserves the cursor', () => {
    const requestBody: StockScreenerRequest = {
      criteria: [
        {
          metric: 'market_cap',
          operator: 'gte',
          value: '1000000000',
        },
      ],
      sort_by: 'market_cap',
      sort_direction: 'desc',
      limit: 25,
      cursor: 'next-page',
    };
    const response: StockScreenerRead = {
      as_of: '2026-09-02T00:00:00Z',
      returned_count: 0,
      next_cursor: 'after-next-page',
      results: [],
      coverage: [],
    };

    service.screenStocks(requestBody).subscribe((result) => {
      expect(result).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/screeners/stocks`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBe(requestBody);
    expect(request.request.body.cursor).toBe('next-page');
    request.flush(response);
  });
});