import { HttpErrorResponse } from '@angular/common/http';
import { MonoTypeOperatorFunction, catchError, throwError } from 'rxjs';

export const ERROR_CODES = {
  stepValidationFailed: 'STEP_VALIDATION_FAILED',
  stepNotCurrent: 'STEP_NOT_CURRENT',
  onboardingNotConfigured: 'ONBOARDING_NOT_CONFIGURED',
  walletNotActive: 'WALLET_NOT_ACTIVE',
} as const;

const HTTP_UNAUTHORIZED = 401;
const HTTP_FORBIDDEN = 403;
const HTTP_NOT_FOUND = 404;
const HTTP_CONFLICT = 409;
const NETWORK_FAILURE_STATUS = 0;

export type ApiErrorKind =
  | 'validation'
  | 'not-configured'
  | 'not-found'
  | 'conflict'
  | 'unauthorized'
  | 'forbidden'
  | 'network'
  | 'unknown';

export interface FieldError {
  readonly field: string;
  readonly rule: string;
  readonly message: string;
}

export interface ApiError {
  readonly kind: ApiErrorKind;
  readonly status: number;
  readonly code: string | null;
  readonly fieldErrors: readonly FieldError[];
  readonly pendingStepIds: readonly string[];
  readonly nextAction: string | null;
}

type JsonRecord = Readonly<Record<string, unknown>>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isFieldError(value: unknown): value is FieldError {
  return (
    isRecord(value) &&
    typeof value['field'] === 'string' &&
    typeof value['rule'] === 'string' &&
    typeof value['message'] === 'string'
  );
}

function stringOrNull(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function arrayOf<T>(value: unknown, guard: (item: unknown) => item is T): readonly T[] {
  return Array.isArray(value) ? value.filter(guard) : [];
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function kindOf(status: number, code: string | null): ApiErrorKind {
  if (code === ERROR_CODES.stepValidationFailed) return 'validation';
  if (code === ERROR_CODES.onboardingNotConfigured) return 'not-configured';
  if (status === NETWORK_FAILURE_STATUS) return 'network';
  if (status === HTTP_UNAUTHORIZED) return 'unauthorized';
  if (status === HTTP_FORBIDDEN) return 'forbidden';
  if (status === HTTP_NOT_FOUND) return 'not-found';
  if (status === HTTP_CONFLICT) return 'conflict';
  return 'unknown';
}

/** Traduce una respuesta HTTP fallida al contrato de errores de la API: `{detail: {code, message, ...}}`. */
export function toApiError(error: unknown): ApiError {
  if (!(error instanceof HttpErrorResponse)) {
    return { kind: 'unknown', status: NETWORK_FAILURE_STATUS, code: null, fieldErrors: [], pendingStepIds: [], nextAction: null };
  }
  const body: unknown = error.error;
  const detail: unknown = isRecord(body) ? body['detail'] : null;
  const code = isRecord(detail) ? stringOrNull(detail['code']) : null;
  return {
    kind: kindOf(error.status, code),
    status: error.status,
    code,
    fieldErrors: isRecord(detail) ? arrayOf(detail['errors'], isFieldError) : [],
    pendingStepIds: isRecord(detail) ? arrayOf(detail['pending_step_ids'], isString) : [],
    nextAction: isRecord(detail) ? stringOrNull(detail['next_action']) : null,
  };
}

export function mapApiError<T>(): MonoTypeOperatorFunction<T> {
  return catchError((error: unknown) => throwError(() => toApiError(error)));
}
