import { environment } from "../../../environments/environment";
import { ApiError } from "../errors/errors";

const apiBaseUrl = environment.apiBaseUrl;

if (!apiBaseUrl) {
  throw new Error("environment.apiBaseUrl must be configured.");
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw await ApiError.fromResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}