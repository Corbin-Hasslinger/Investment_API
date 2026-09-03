import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { CompanyResearchRead } from '../models/research-model';
import { ResearchApiService } from './research-api-service';

describe('ResearchApiService', () => {
  const baseUrl = 'https://api.test';
  let service: ResearchApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(ResearchApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('normalizes and encodes the research symbol and returns company research', () => {
    const response: CompanyResearchRead = {
      company: {
        symbol: 'RDS-A',
        name: 'Example Energy',
        exchange: null,
        industry: null,
        country: null,
        currency: null,
        ipo_date: null,
        website: null,
        logo_url: null,
        market_cap: null,
        shares_outstanding: null,
      },
      valuation: {
        pe_ratio_ttm: null,
        price_to_book: null,
        price_to_sales_ttm: null,
        price_to_free_cash_flow_ttm: null,
      },
      performance: {
        fifty_two_week_high: null,
        fifty_two_week_low: null,
        beta: null,
        return_3_month_percent: null,
        return_1_year_percent: null,
      },
      fundamentals: {
        eps_ttm: null,
        revenue_growth_yoy_percent: null,
        eps_growth_yoy_percent: null,
        gross_margin_percent: null,
        operating_margin_percent: null,
        net_margin_percent: null,
        return_on_equity_percent: null,
        current_ratio: null,
        debt_to_equity: null,
      },
      news: [],
    };

    service.getCompanyResearch(' rds/a ').subscribe((research) => {
      expect(research).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/research/company/RDS-A`);
    expect(request.request.method).toBe('GET');
    request.flush(response);
  });
});