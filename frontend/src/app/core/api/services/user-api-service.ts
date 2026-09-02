import { HttpClient } from "@angular/common/http";
import { inject, Injectable } from "@angular/core";
import { API_BASE_URL } from "../api-base-url";
import { Observable } from "rxjs";
import { CurrentUserRead } from "../models/user-model";

@Injectable({
  providedIn: 'root',
})
export class UserApiService {
  private readonly http =
    inject(HttpClient);

  private readonly baseUrl =
    inject(API_BASE_URL);

  getCurrentUser():
    Observable<CurrentUserRead> {
    return this.http.get<CurrentUserRead>(
      `${this.baseUrl}/users/me`,
    );
  }
}