import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AtlasApiError, FastApiValidationError } from './api-error';
import { apiErrorInterceptor } from './api-error.interceptor';

describe('apiErrorInterceptor', () => {
  let http: HttpTestingController;
  let client: HttpClient;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([apiErrorInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    client = TestBed.inject(HttpClient);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('maps 404 portfolio_not_found domain errors', () => {
    let actual: AtlasApiError | undefined;
    client.get('/portfolios/missing').subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/portfolios/missing');
    request.flush(
      { error: { code: 'portfolio_not_found', message: 'Portfolio not found' } },
      { status: 404, statusText: 'Not Found' },
    );

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(404);
    expect(actual?.code).toBe('portfolio_not_found');
  });

  it('maps 409 duplicate domain errors with the backend code and message', () => {
    let actual: AtlasApiError | undefined;
    client.post('/portfolios/portfolio-1/positions', {}).subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/portfolios/portfolio-1/positions');
    request.flush(
      { error: { code: 'position_duplicate', message: 'Position already exists' } },
      { status: 409, statusText: 'Conflict' },
    );

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(409);
    expect(actual?.code).toBe('position_duplicate');
    expect(actual?.message).toBe('Position already exists');
  });

  it('maps 422 FastAPI validation errors and preserves validation details', () => {
    const validationErrors: FastApiValidationError[] = [
      {
        type: 'string_too_short',
        loc: ['body', 'name'],
        msg: 'String should have at least 1 character',
      },
    ];
    let actual: AtlasApiError | undefined;

    client.post('/portfolios', {}).subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/portfolios');
    request.flush(
      { detail: validationErrors },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(422);
    expect(actual?.code).toBe('validation_error');
    expect(actual?.validationErrors).toBe(validationErrors);
  });

  it('maps 429 errors to upstream_rate_limited when the backend provides that code', () => {
    let actual: AtlasApiError | undefined;
    client.get('/market/quote/AAPL').subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/market/quote/AAPL');
    request.flush(
      { error: { code: 'upstream_rate_limited', message: 'Rate limit exceeded' } },
      { status: 429, statusText: 'Too Many Requests' },
    );

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(429);
    expect(actual?.code).toBe('upstream_rate_limited');
  });

  it('maps 503 errors to upstream_unavailable when the backend provides that code', () => {
    let actual: AtlasApiError | undefined;
    client.get('/research/company/AAPL').subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/research/company/AAPL');
    request.flush(
      { error: { code: 'upstream_unavailable', message: 'Upstream unavailable' } },
      { status: 503, statusText: 'Service Unavailable' },
    );

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(503);
    expect(actual?.code).toBe('upstream_unavailable');
  });

  it('maps status 0 responses to network_error', () => {
    let actual: AtlasApiError | undefined;
    client.get('/users/me').subscribe({
      error: (error: AtlasApiError) => {
        actual = error;
      },
    });

    const request = http.expectOne('/users/me');
    request.error(new ProgressEvent('error'), {
      status: 0,
      statusText: 'Unknown Error',
    });

    expect(actual).toBeInstanceOf(AtlasApiError);
    expect(actual?.status).toBe(0);
    expect(actual?.code).toBe('network_error');
  });
});