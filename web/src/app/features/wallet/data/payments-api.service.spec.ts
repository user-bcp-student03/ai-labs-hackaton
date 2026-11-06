import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { APP_CONFIG } from '../../../core/config/app-config';
import { userIdentityInterceptor } from '../../../core/http/user-identity.interceptor';
import { PaymentError } from './payment-error';
import { PaymentsApiService } from './payments-api.service';
import { PaymentIntent } from './payments.models';

const INTENT: PaymentIntent = { intent_id: 'i-1', amount_cents: 1050, recipient: 'contact-demo', channel: 'web' };

describe('PaymentsApiService', () => {
  let service: PaymentsApiService;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: APP_CONFIG, useValue: { apiBaseUrl: '/wallet-api', testUserId: 'TEST-user-spec' } },
        provideHttpClient(withInterceptors([userIdentityInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(PaymentsApiService);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('openConfirmation hace POST /payments/confirmations con la identidad del onboarding', async () => {
    const body = { recipient: 'contact-demo' as const, amount_cents: 1050, channel: 'web' };
    const result = firstValueFrom(service.openConfirmation(body));
    const request = controller.expectOne('/wallet-api/payments/confirmations');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(body);
    expect(request.request.headers.get('X-Payer-Id')).toBe('TEST-user-spec');
    request.flush({ can_confirm: true, intent_id: 'i-1' });
    expect((await result).intent_id).toBe('i-1');
  });

  it('abandonConfirmation hace POST al abandono del intent_id', async () => {
    const result = firstValueFrom(service.abandonConfirmation('i-1'), { defaultValue: undefined });
    const request = controller.expectOne('/wallet-api/payments/confirmations/i-1/abandon');
    expect(request.request.method).toBe('POST');
    request.flush(null, { status: 204, statusText: 'No Content' });
    await result;
  });

  it('submitPayment envía el intent_id en el cuerpo', async () => {
    const result = firstValueFrom(service.submitPayment(INTENT));
    const request = controller.expectOne('/wallet-api/payments');
    expect(request.request.body).toEqual(INTENT);
    request.flush({ payment_id: 'p-1', status: 'PENDING' });
    expect((await result).payment_id).toBe('p-1');
  });

  it('submitPayment traduce el 422 de monto sobre el límite', async () => {
    const result = firstValueFrom(service.submitPayment(INTENT)).catch((error: PaymentError) => error);
    controller
      .expectOne('/wallet-api/payments')
      .flush(
        { detail: { code: 'amount_exceeds_limit', limit_cents: 5000, message: 'm' } },
        { status: 422, statusText: 'Unprocessable' },
      );
    const error = (await result) as PaymentError;
    expect(error.kind).toBe('amount-exceeds-limit');
    expect(error.limitCents).toBe(5000);
  });

  it('getPayment, retryPayment y listPayments usan sus rutas', async () => {
    const get = firstValueFrom(service.getPayment('p 1'));
    controller.expectOne('/wallet-api/payments/p%201').flush({ payment_id: 'p 1' });
    await get;
    const retry = firstValueFrom(service.retryPayment('p-1'));
    const retryRequest = controller.expectOne('/wallet-api/payments/p-1/retries');
    expect(retryRequest.request.method).toBe('POST');
    retryRequest.flush({ payment_id: 'p-2' });
    await retry;
    const list = firstValueFrom(service.listPayments());
    controller.expectOne('/wallet-api/payments').flush([]);
    expect(await list).toEqual([]);
  });
});
