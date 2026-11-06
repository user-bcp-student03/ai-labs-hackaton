import { TestBed } from '@angular/core/testing';
import { Router, UrlTree, provideRouter } from '@angular/router';
import { Observable, firstValueFrom, of, throwError } from 'rxjs';
import { ApiError } from '../../../core/http/api-error';
import { WalletApiService } from '../data/wallet-api.service';
import { activeWalletGuard } from './active-wallet.guard';

function apiError(status: number, kind: ApiError['kind']): ApiError {
  return { kind, status, code: null, fieldErrors: [], pendingStepIds: [], nextAction: null };
}

async function runGuard(checkPaymentsEntry: () => Observable<{ allowed: boolean }>): Promise<boolean | UrlTree> {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), { provide: WalletApiService, useValue: { checkPaymentsEntry } }],
  });
  const result = TestBed.runInInjectionContext(() => activeWalletGuard({} as never, {} as never));
  return firstValueFrom(result as Observable<boolean | UrlTree>);
}

describe('activeWalletGuard', () => {
  it('deja pasar con wallet activa', async () => {
    expect(await runGuard(() => of({ allowed: true }))).toBe(true);
  });

  it('redirige a /onboarding si la API responde 403 WALLET_NOT_ACTIVE', async () => {
    const outcome = await runGuard(() => throwError(() => apiError(403, 'forbidden')));
    expect(TestBed.inject(Router).serializeUrl(outcome as UrlTree)).toBe('/onboarding');
  });

  it('redirige a /onboarding ante un fallo de red o del servidor (deniega por defecto)', async () => {
    const outcome = await runGuard(() => throwError(() => apiError(0, 'network')));
    expect(TestBed.inject(Router).serializeUrl(outcome as UrlTree)).toBe('/onboarding');
  });

  it('redirige a /onboarding si la respuesta no autoriza el acceso', async () => {
    const outcome = await runGuard(() => of({ allowed: false }));
    expect(TestBed.inject(Router).serializeUrl(outcome as UrlTree)).toBe('/onboarding');
  });
});
