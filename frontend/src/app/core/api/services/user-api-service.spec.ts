import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { API_BASE_URL } from '../api-base-url';
import { CurrentUserRead } from '../models/user-model';
import { UserApiService } from './user-api-service';

describe('UserApiService', () => {
  const baseUrl = 'https://api.test';
  let service: UserApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: baseUrl },
      ],
    });

    service = TestBed.inject(UserApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('gets the current user from /users/me', () => {
    const response: CurrentUserRead = {
      id: 'user-1',
      email: 'person@example.com',
    };

    let actual: CurrentUserRead | undefined;
    service.getCurrentUser().subscribe((user) => {
      actual = user;
    });

    const request = http.expectOne(`${baseUrl}/users/me`);
    expect(request.request.method).toBe('GET');
    request.flush(response);

    expect(actual).toEqual(response);
  });
});