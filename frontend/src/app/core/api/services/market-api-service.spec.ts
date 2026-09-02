import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { StockQuote } from '../models/market-model';
import { MarketApiService } from './market-api-service';

describe('MarketApiService', () => {
  const baseUrl = 'https://api.test';
  let service: MarketApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(MarketApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('normalizes and encodes the quote symbol and returns the quote', () => {
    const response: StockQuote = {
      symbol: 'BRK.B',
      current_price: '400.00',
      price_change: '1.00',
      percent_change: '0.25',
      high_price: '405.00',
      low_price: '395.00',
      open_price: '399.00',
      previous_close_price: '399.00',
      timestamp: 1788379200,
    };

    service.getQuote(' brk/b ').subscribe((quote) => {
      expect(quote).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/market/quote/BRK%2FB`);
    expect(request.request.method).toBe('GET');
    request.flush(response);
  });
});