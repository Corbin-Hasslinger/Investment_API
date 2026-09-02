export interface AtlasErrorBody {
  error: {
    code: string;
    message: string;
  };
}

export interface FastApiValidationError {
  type: string;
  loc: Array<string | number>;
  msg: string;
}

export interface FastApiValidationBody {
  detail: FastApiValidationError[];
}

export class AtlasApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly validationErrors:
      FastApiValidationError[] = [],
  ) {
    super(message);
    this.name = 'AtlasApiError';
  }
}