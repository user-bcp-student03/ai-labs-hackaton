import { HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom, throwError } from 'rxjs';
import { PaymentError, mapPaymentError, toPaymentError } from './payment-error';

function httpError(status: number, body: unknown): HttpErrorResponse {
  return new HttpErrorResponse({ status, error: body });
}

describe('toPaymentError', () => {
  it('reconoce el 422 de monto sobre el límite con su mensaje y límite', () => {
    const error = toPaymentError(
      httpError(422, { detail: { code: 'amount_exceeds_limit', limit_cents: 5000, message: 'Máximo S/ 50.00' } }),
    );
    expect(error.kind).toBe('amount-exceeds-limit');
    expect(error.limitCents).toBe(5000);
    expect(error.message).toBe('Máximo S/ 50.00');
  });

  it('reconoce el 409 de intento previo con sus acciones y descarta las inválidas', () => {
    const error = toPaymentError(
      httpError(409, {
        detail: {
          code: 'previous_in_progress',
          message: 'En proceso',
          previous_payment_id: 'p-1',
          actions: [
            { id: 'view_previous', label: 'Ver estado', payment_id: 'p-1' },
            { id: 'back', label: 'Volver', payment_id: null },
            { id: 'hack', label: 'x' },
            'texto',
          ],
        },
      }),
    );
    expect(error.kind).toBe('previous-in-progress');
    expect(error.previousPaymentId).toBe('p-1');
    expect(error.actions.map((action) => action.id)).toEqual(['view_previous', 'back']);
  });

  it.each([
    [404, 'not-found'],
    [0, 'network'],
    [500, 'unknown'],
  ] as const)('clasifica el estado %i como %s sin exponer detalles', (status, kind) => {
    const error = toPaymentError(httpError(status, 'texto plano'));
    expect(error.kind).toBe(kind);
    expect(error.message).toBeNull();
    expect(error.actions).toEqual([]);
  });

  it('un error que no es HTTP se trata como desconocido', () => {
    expect(toPaymentError(new Error('boom')).kind).toBe('unknown');
  });

  it('un 422 con otro código no se confunde con monto sobre el límite', () => {
    expect(toPaymentError(httpError(422, { detail: [{ msg: 'x' }] })).kind).toBe('unknown');
  });
});

describe('mapPaymentError', () => {
  it('convierte el error HTTP en PaymentError', async () => {
    const stream = throwError(() => httpError(404, { detail: 'x' })).pipe(mapPaymentError());
    const error: PaymentError = await firstValueFrom(stream).catch((caught: PaymentError) => caught);
    expect(error.kind).toBe('not-found');
  });
});
