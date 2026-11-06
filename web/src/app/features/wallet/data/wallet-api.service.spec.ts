import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { APP_CONFIG } from '../../../core/config/app-config';
import { ApiError } from '../../../core/http/api-error';
import { userIdentityInterceptor } from '../../../core/http/user-identity.interceptor';
import { WalletApiService } from './wallet-api.service';

describe('WalletApiService', () => {
  let service: WalletApiService;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: APP_CONFIG, useValue: { apiBaseUrl: '/wallet-api', testUserId: 'TEST-user-spec' } },
        provideHttpClient(withInterceptors([userIdentityInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(WalletApiService);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('getWallet hace GET /wallet con X-Payer-Id', async () => {
    const result = firstValueFrom(service.getWallet());
    const request = controller.expectOne('/wallet-api/wallet');
    expect(request.request.headers.get('X-Payer-Id')).toBe('TEST-user-spec');
    request.flush({ status: 'activo', activated_at: '2026-11-06T10:00:00Z' });
    expect((await result).status).toBe('activo');
  });

  it('checkPaymentsEntry hace GET /wallet/payments-entry', async () => {
    const result = firstValueFrom(service.checkPaymentsEntry());
    controller.expectOne('/wallet-api/wallet/payments-entry').flush({ allowed: true });
    expect(await result).toEqual({ allowed: true });
  });

  it('checkPaymentsEntry traduce el 403 WALLET_NOT_ACTIVE', async () => {
    const result = firstValueFrom(service.checkPaymentsEntry()).catch((error: ApiError) => error);
    controller.expectOne('/wallet-api/wallet/payments-entry').flush(
      { detail: { code: 'WALLET_NOT_ACTIVE', message: 'x', next_action: 'complete_onboarding' } },
      { status: 403, statusText: 'Forbidden' },
    );
    const error = (await result) as ApiError;
    expect(error.kind).toBe('forbidden');
    expect(error.nextAction).toBe('complete_onboarding');
  });
});
