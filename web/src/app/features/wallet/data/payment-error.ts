import { HttpErrorResponse } from '@angular/common/http';
import { MonoTypeOperatorFunction, catchError, throwError } from 'rxjs';
import { PaymentAction, PaymentActionId } from './payments.models';

const HTTP_NOT_FOUND = 404;
const HTTP_CONFLICT = 409;
const HTTP_UNPROCESSABLE = 422;
const NETWORK_FAILURE_STATUS = 0;

export const PAYMENT_ERROR_CODES = {
  amountExceedsLimit: 'amount_exceeds_limit',
  previousInProgress: 'previous_in_progress',
} as const;

export type PaymentErrorKind = 'amount-exceeds-limit' | 'previous-in-progress' | 'not-found' | 'network' | 'unknown';

export interface PaymentError {
  readonly kind: PaymentErrorKind;
  readonly status: number;
  /** Mensaje accionable de la API (contenido configurable); null si no vino. */
  readonly message: string | null;
  readonly limitCents: number | null;
  readonly previousPaymentId: string | null;
  readonly actions: readonly PaymentAction[];
}

type JsonRecord = Readonly<Record<string, unknown>>;

const ACTION_IDS: readonly string[] = ['retry', 'back', 'view_previous'] satisfies PaymentActionId[];

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function stringOrNull(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === 'number' ? value : null;
}

function toAction(value: unknown): PaymentAction | null {
  if (!isRecord(value) || typeof value['id'] !== 'string' || typeof value['label'] !== 'string') return null;
  if (!ACTION_IDS.includes(value['id'])) return null;
  return { id: value['id'] as PaymentActionId, label: value['label'], payment_id: stringOrNull(value['payment_id']) };
}

function toActions(value: unknown): readonly PaymentAction[] {
  if (!Array.isArray(value)) return [];
  return value.map(toAction).filter((action): action is PaymentAction => action !== null);
}

function kindOf(status: number, code: string | null): PaymentErrorKind {
  if (status === HTTP_UNPROCESSABLE && code === PAYMENT_ERROR_CODES.amountExceedsLimit) return 'amount-exceeds-limit';
  if (status === HTTP_CONFLICT && code === PAYMENT_ERROR_CODES.previousInProgress) return 'previous-in-progress';
  if (status === HTTP_NOT_FOUND) return 'not-found';
  if (status === NETWORK_FAILURE_STATUS) return 'network';
  return 'unknown';
}

/** Traduce un error HTTP de pagos (`{detail: {code, message, ...}}`) sin exponer detalles técnicos. */
export function toPaymentError(error: unknown): PaymentError {
  if (!(error instanceof HttpErrorResponse)) {
    return { kind: 'unknown', status: NETWORK_FAILURE_STATUS, message: null, limitCents: null, previousPaymentId: null, actions: [] };
  }
  const body: unknown = error.error;
  const detail: JsonRecord = isRecord(body) && isRecord(body['detail']) ? body['detail'] : {};
  return {
    kind: kindOf(error.status, stringOrNull(detail['code'])),
    status: error.status,
    message: stringOrNull(detail['message']),
    limitCents: numberOrNull(detail['limit_cents']),
    previousPaymentId: stringOrNull(detail['previous_payment_id']),
    actions: toActions(detail['actions']),
  };
}

export function mapPaymentError<T>(): MonoTypeOperatorFunction<T> {
  return catchError((error: unknown) => throwError(() => toPaymentError(error)));
}
