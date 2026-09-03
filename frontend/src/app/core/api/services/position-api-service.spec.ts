import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../api-base-url';
import { PaginatedResult } from '../models/pagination-model';
import { PositionCreate, PositionRead, PositionUpdate } from '../models/position-model';
import { PositionApiService } from './position-api-service';

describe('PositionApiService', () => {
  const baseUrl = 'https://api.test';
  let service: PositionApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(PositionApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('gets positions from the nested portfolio URL with pagination', () => {
    const response: PaginatedResult<PositionRead> = {
      items: [],
      total: 0,
      page: 3,
      page_size: 50,
    };

    service.getPositions('portfolio-1', { page: 3, pageSize: 50 }).subscribe((result) => {
      expect(result).toEqual(response);
    });

    const request = http.expectOne((req) => req.url === `${baseUrl}/portfolios/portfolio-1/positions`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('page')).toBe('3');
    expect(request.request.params.get('page_size')).toBe('50');
    request.flush(response);
  });

  it('posts the create payload to the nested portfolio URL', () => {
    const payload: PositionCreate = {
      symbol: 'AAPL',
      shares: '4',
      average_cost: '150.00',
    };
    const response: PositionRead = {
      ...payload,
      id: 'position-1',
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-02T00:00:00Z',
    };

    service.createPosition('portfolio-1', payload).subscribe((position) => {
      expect(position).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1/positions`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBe(payload);
    request.flush(response);
  });

  it('patches the update payload on a nested position URL', () => {
    const payload: PositionUpdate = {
      shares: '8',
    };
    const response: PositionRead = {
      id: 'position-1',
      symbol: 'AAPL',
      shares: '8',
      average_cost: '150.00',
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-02T01:00:00Z',
    };

    service.updatePosition('portfolio-1', 'position-1', payload).subscribe((position) => {
      expect(position).toEqual(response);
    });

    const request = http.expectOne(`${baseUrl}/portfolios/portfolio-1/positions/position-1`);
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toBe(payload);
    request.flush(response);
  });
});