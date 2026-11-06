import { HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom, throwError } from 'rxjs';
import { ApiError, mapApiError, toApiError } from './api-error';

function httpError(status: number, body: unknown): HttpErrorResponse {
  return new HttpErrorResponse({ status, error: body });
}

describe('toApiError', () => {
  it('lee los errores de campo de un 422 STEP_VALIDATION_FAILED', () => {
    const error = toApiError(
      httpError(422, {
        detail: {
          code: 'STEP_VALIDATION_FAILED',
          message: 'Corrige los datos indicados para continuar.',
          errors: [{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }],
        },
      }),
    );
    expect(error.kind).toBe('validation');
    expect(error.fieldErrors).toEqual([{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }]);
  });

  it('descarta elementos de errores que no tienen la forma esperada', () => {
    const error = toApiError(
      httpError(422, { detail: { code: 'STEP_VALIDATION_FAILED', errors: [{ field: 1 }, 'x', null] } }),
    );
    expect(error.fieldErrors).toEqual([]);
  });

  it('reconoce el flujo no configurado (503)', () => {
    expect(toApiError(httpError(503, { detail: { code: 'ONBOARDING_NOT_CONFIGURED', message: 'x' } })).kind).toBe(
      'not-configured',
    );
  });

  it('devuelve los pasos pendientes de ONBOARDING_INCOMPLETE y la acción siguiente de WALLET_NOT_ACTIVE', () => {
    const incomplete = toApiError(
      httpError(409, { detail: { code: 'ONBOARDING_INCOMPLETE', pending_step_ids: ['contacto', 7] } }),
    );
    expect(incomplete.kind).toBe('conflict');
    expect(incomplete.pendingStepIds).toEqual(['contacto']);
    const notActive = toApiError(
      httpError(403, { detail: { code: 'WALLET_NOT_ACTIVE', next_action: 'complete_onboarding' } }),
    );
    expect(notActive.kind).toBe('forbidden');
    expect(notActive.nextAction).toBe('complete_onboarding');
  });

  it.each([
    [0, 'network'],
    [401, 'unauthorized'],
    [404, 'not-found'],
    [500, 'unknown'],
  ] as const)('clasifica el estado %i como %s aunque el cuerpo no sea JSON de la API', (status, kind) => {
    const error = toApiError(httpError(status, 'texto plano'));
    expect(error.kind).toBe(kind);
    expect(error.code).toBeNull();
    expect(error.fieldErrors).toEqual([]);
  });

  it('un 401 de la API con detail de texto no rompe el análisis', () => {
    expect(toApiError(httpError(401, { detail: 'identidad requerida' })).kind).toBe('unauthorized');
  });

  it('un error que no es HTTP se trata como desconocido', () => {
    expect(toApiError(new Error('boom')).kind).toBe('unknown');
  });
});

describe('mapApiError', () => {
  it('convierte el error HTTP del flujo en un ApiError', async () => {
    const stream = throwError(() => httpError(409, { detail: { code: 'STEP_NOT_CURRENT' } })).pipe(mapApiError());
    const error: ApiError = await firstValueFrom(stream).catch((caught: ApiError) => caught);
    expect(error.kind).toBe('conflict');
    expect(error.code).toBe('STEP_NOT_CURRENT');
  });
});
