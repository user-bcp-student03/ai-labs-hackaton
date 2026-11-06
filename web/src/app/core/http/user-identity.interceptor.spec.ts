import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { APP_CONFIG, AppConfig } from '../config/app-config';
import { userIdentityInterceptor } from './user-identity.interceptor';

const TEST_CONFIG: AppConfig = { apiBaseUrl: '/wallet-api', testUserId: 'TEST-user-spec' };

describe('userIdentityInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: APP_CONFIG, useValue: TEST_CONFIG },
        provideHttpClient(withInterceptors([userIdentityInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('agrega X-Payer-Id con la identidad de prueba a las llamadas a la API', () => {
    http.get('/wallet-api/wallet').subscribe();
    const request = controller.expectOne('/wallet-api/wallet');
    expect(request.request.headers.get('X-Payer-Id')).toBe('TEST-user-spec');
    request.flush({});
  });

  it('no agrega la identidad a otras URL', () => {
    http.get('https://example.test/otro').subscribe();
    const request = controller.expectOne('https://example.test/otro');
    expect(request.request.headers.has('X-Payer-Id')).toBe(false);
    request.flush({});
  });

  it('usa un identificador que cumple el patrón que acepta la API y el prefijo TEST-', () => {
    expect(TEST_CONFIG.testUserId).toMatch(/^[A-Za-z0-9._:-]{1,64}$/);
    expect(TEST_CONFIG.testUserId.startsWith('TEST-')).toBe(true);
  });
});
