import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AtlasApiError, FastApiValidationError } from './api-error';

interface AtlasDomainErrorBody {
	error?: {
		code?: unknown;
		message?: unknown;
	};
}

interface FastApiValidationErrorBody {
	detail?: unknown;
}

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => {
	return next(request).pipe(
		catchError((error: unknown) => {
			if (error instanceof HttpErrorResponse) {
				return throwError(() => normalizeHttpError(error));
			}

			return throwError(() => error);
		}),
	);
};

function normalizeHttpError(error: HttpErrorResponse): AtlasApiError {
	if (error.status === 0) {
		return new AtlasApiError(0, 'network_error', 'Unable to reach the API.');
	}

	const errorBody = error.error as AtlasDomainErrorBody | FastApiValidationErrorBody | null;
	const domainError = (errorBody as AtlasDomainErrorBody | null)?.error;

	if (typeof domainError?.code === 'string' && typeof domainError.message === 'string') {
		return new AtlasApiError(error.status, domainError.code, domainError.message);
	}

	const detail = (errorBody as FastApiValidationErrorBody | null)?.detail;

	if (Array.isArray(detail)) {
		return new AtlasApiError(
			error.status,
			'validation_error',
			'Validation error',
			detail as FastApiValidationError[],
		);
	}

	return new AtlasApiError(error.status, 'unexpected_error', error.message || 'Unexpected API error');
}
