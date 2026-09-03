import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { PortfolioAnalyticsRead } from '../models/analytics-model';
import { PaginatedResult } from '../models/pagination-model';
import { PortfolioCreate, PortfolioRead, PortfolioUpdate } from '../models/portfolio-model';
import { PortfolioApiService } from './portfolio-api-service';

describe('PortfolioApiService', () => {
  const baseUrl = 'https://api.test';
  let service: PortfolioApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(PortfolioApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('gets portfolios with pagination query params', () => {
    const response: PaginatedResult<PortfolioRead> = {
      items: [],
      total: 0,
      page: 2,
      page_size: 10,
    };

    let actual: PaginatedResult<PortfolioRead> | undefined;
    service.getPortfolios({ page: 2, pageSize: 10 }).subscribe((result) => {
      actual = result;
    });

    const request = http.expectOne((req) => req.url === `${baseUrl}/portfolios`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('page')).toBe('2');
    expect(request.request.params.get('page_size')).toBe('10');
    request.flush(response);

    expect(actual).toEqual(response);
  });

  it('posts the create payload', () => {
    const payload: PortfolioCreate = {
      name: 'Core',
      description: 'Long-term holdings',
    };
    const response: PortfolioRead = {
      name: payload.name,
      description: payload.description ?? null,
      id: 'portfolio-1',
      user_id: 'user-1',
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-02T00:00:00Z',
    };

    service.createPortfolio(payload).subscribe((portfolio) => {
      expect(portfolio).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBe(payload);
    request.flush(response);
  });

  it('patches the update payload', () => {
    const payload: PortfolioUpdate = {
      name: 'Updated',
      description: null,
    };
    const response: PortfolioRead = {
      id: 'portfolio-1',
      user_id: 'user-1',
      name: 'Updated',
      description: null,
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-02T01:00:00Z',
    };

    service.updatePortfolio('portfolio-1', payload).subscribe((portfolio) => {
      expect(portfolio).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1`);
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toBe(payload);
    request.flush(response);
  });

  it('deletes a portfolio with DELETE', () => {
    service.deletePortfolio('portfolio-1').subscribe((result) => {
      expect(result).toBeNull();
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1`);
    expect(request.request.method).toBe('DELETE');
    request.flush(null);
  });

  it('gets portfolio analytics from the analytics URL', () => {
    const response: PortfolioAnalyticsRead = {
      portfolio_id: 'portfolio-1',
      total_market_value: '100.00',
      total_cost_basis: '80.00',
      total_unrealized_gain_loss: '20.00',
      total_unrealized_gain_loss_percent: '25.00',
      positions: [],
    };

    service.getAnalytics('portfolio-1').subscribe((analytics) => {
      expect(analytics).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1/analytics`);
    expect(request.request.method).toBe('GET');
    request.flush(response);
  });
});