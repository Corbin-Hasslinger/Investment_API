type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
  }

  static async fromResponse(response: Response): Promise<ApiError> {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;

    return new ApiError(
      response.status,
      body?.error?.code ?? "request_failed",
      body?.error?.message ?? "The request could not be completed.",
    );
  }
}