import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { PortfolioExplanationRead, SecurityExplanationRead } from '../models/explanation-model';
import { ExplanationApiService } from './explanation-api-service';

describe('ExplanationApiService', () => {
  const baseUrl = 'https://api.test';
  let service: ExplanationApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(ExplanationApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('posts to the portfolio explanation URL with no body', () => {
    const response: PortfolioExplanationRead = {
      portfolio_id: 'portfolio-1',
      data_retrieved_at: '2026-09-02T00:00:00Z',
      generated_at: '2026-09-02T00:01:00Z',
      explanation: {
        summary: 'Balanced.',
        strengths: [],
        risks: [],
        concentration: [],
        performance: [],
        limitations: [],
      },
    };

    service.explainPortfolio('portfolio-1').subscribe((explanation) => {
      expect(explanation).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1/explanations`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeNull();
    request.flush(response);
  });

  it('posts to the normalized security explanation URL with no body', () => {
    const response: SecurityExplanationRead = {
      symbol: 'BRK/B',
      data_retrieved_at: '2026-09-02T00:00:00Z',
      generated_at: '2026-09-02T00:01:00Z',
      explanation: {
        summary: 'Durable.',
        valuation: [],
        growth_and_profitability: [],
        financial_health: [],
        performance: [],
        recent_developments: [],
        risks: [],
        limitations: [],
      },
    };

    service.explainSecurity(' brk/b ').subscribe((explanation) => {
      expect(explanation).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/securities/BRK%2FB/explanations`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeNull();
    request.flush(response);
  });
});