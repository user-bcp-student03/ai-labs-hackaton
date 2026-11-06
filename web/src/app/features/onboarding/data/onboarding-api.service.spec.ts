import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { APP_CONFIG } from '../../../core/config/app-config';
import { ApiError } from '../../../core/http/api-error';
import { userIdentityInterceptor } from '../../../core/http/user-identity.interceptor';
import { EXAMPLE_FLOW, onboardingAt } from '../onboarding.fixtures';
import { OnboardingApiService } from './onboarding-api.service';

describe('OnboardingApiService', () => {
  let service: OnboardingApiService;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: APP_CONFIG, useValue: { apiBaseUrl: '/wallet-api', testUserId: 'TEST-user-spec' } },
        provideHttpClient(withInterceptors([userIdentityInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(OnboardingApiService);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('getFlow hace GET /onboarding/flow', async () => {
    const result = firstValueFrom(service.getFlow());
    const request = controller.expectOne('/wallet-api/onboarding/flow');
    expect(request.request.method).toBe('GET');
    request.flush(EXAMPLE_FLOW);
    expect(await result).toEqual(EXAMPLE_FLOW);
  });

  it('startOrResume hace POST /onboarding con la identidad de prueba', async () => {
    const view = onboardingAt(EXAMPLE_FLOW, 0);
    const result = firstValueFrom(service.startOrResume());
    const request = controller.expectOne('/wallet-api/onboarding');
    expect(request.request.method).toBe('POST');
    expect(request.request.headers.get('X-Payer-Id')).toBe('TEST-user-spec');
    request.flush(view, { status: 201, statusText: 'Created' });
    expect(await result).toEqual(view);
  });

  it('getCurrent hace GET /onboarding/current', async () => {
    const result = firstValueFrom(service.getCurrent());
    controller.expectOne('/wallet-api/onboarding/current').flush(onboardingAt(EXAMPLE_FLOW, 1));
    expect((await result).completed_steps).toBe(1);
  });

  it('submitStep hace PUT con {values} y codifica los identificadores', async () => {
    const result = firstValueFrom(service.submitStep('ob_1', 'datos-personales', { full_name: 'Ana Torres', accept: true }));
    const request = controller.expectOne('/wallet-api/onboarding/ob_1/steps/datos-personales');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({ values: { full_name: 'Ana Torres', accept: true } });
    request.flush(onboardingAt(EXAMPLE_FLOW, 1));
    await result;
  });

  it('submitStep no permite que un identificador altere la ruta', () => {
    service.submitStep('ob/../x', 'a b', {}).subscribe({ error: () => undefined });
    const request = controller.expectOne('/wallet-api/onboarding/ob%2F..%2Fx/steps/a%20b');
    request.flush({}, { status: 404, statusText: 'Not Found' });
  });

  it('close hace POST /onboarding/{id}/close', async () => {
    const result = firstValueFrom(service.close('ob_1'));
    const request = controller.expectOne('/wallet-api/onboarding/ob_1/close');
    expect(request.request.method).toBe('POST');
    request.flush(onboardingAt(EXAMPLE_FLOW, 3, { status: 'COMPLETED', wallet_status: 'activo' }));
    expect((await result).status).toBe('COMPLETED');
  });

  it('traduce un 422 a ApiError con los errores de campo del servidor', async () => {
    const result = firstValueFrom(service.submitStep('ob_1', 'contacto', { phone: '1' })).catch((error: ApiError) => error);
    controller.expectOne('/wallet-api/onboarding/ob_1/steps/contacto').flush(
      {
        detail: {
          code: 'STEP_VALIDATION_FAILED',
          message: 'Corrige los datos indicados para continuar.',
          errors: [{ field: 'phone', rule: 'pattern', message: 'Escribe 9 dígitos que empiecen con 9; por ejemplo: 912345678.' }],
        },
      },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    const error = (await result) as ApiError;
    expect(error.kind).toBe('validation');
    expect(error.fieldErrors[0].field).toBe('phone');
  });

  it('traduce un 503 a flujo no configurado', async () => {
    const result = firstValueFrom(service.getFlow()).catch((error: ApiError) => error);
    controller.expectOne('/wallet-api/onboarding/flow').flush(
      { detail: { code: 'ONBOARDING_NOT_CONFIGURED', message: 'x' } },
      { status: 503, statusText: 'Service Unavailable' },
    );
    expect(((await result) as ApiError).kind).toBe('not-configured');
  });
});
