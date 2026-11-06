import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap, provideRouter } from '@angular/router';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { PaymentError } from '../../data/payment-error';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentResult } from '../../data/payments.models';
import { paymentFixture } from '../../wallet.fixtures';
import { PaymentResultPage } from './payment-result-page';

function paymentError(kind: PaymentError['kind']): PaymentError {
  return { kind, status: 0, message: null, limitCents: null, previousPaymentId: null, actions: [] };
}

const RETRY_ACTIONS = [
  { id: 'retry', label: 'Reintentar', payment_id: null },
  { id: 'back', label: 'Volver', payment_id: null },
] as const;

describe('PaymentResultPage', () => {
  const getPayment = vi.fn<(id: string) => Observable<PaymentResult>>();
  const retryPayment = vi.fn<(id: string) => Observable<PaymentResult>>();

  function setup(id: string | null = 'pay-1') {
    getPayment.mockReset();
    retryPayment.mockReset();
    const params = new BehaviorSubject(convertToParamMap(id ? { paymentId: id } : {}));
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { paramMap: params } },
        { provide: PaymentsApiService, useValue: { getPayment, retryPayment } },
      ],
    });
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    return { params, navigate };
  }

  function render() {
    const fixture = TestBed.createComponent(PaymentResultPage);
    const element = fixture.nativeElement as HTMLElement;
    document.body.appendChild(element);
    fixture.detectChanges();
    const text = () => element.textContent ?? '';
    const labels = () => Array.from(element.querySelectorAll('button')).map((button) => button.textContent?.trim());
    return { fixture, element, text, labels };
  }

  afterEach(() => {
    vi.useRealTimers();
    document.body.innerHTML = '';
  });

  it('muestra pago exitoso con su referencia y sin acciones de reintento', async () => {
    setup();
    getPayment.mockReturnValue(of(paymentFixture()));
    const { fixture, element, text, labels } = render();
    await fixture.whenStable();
    expect(element.querySelector('h1')?.textContent).toBe('Pago exitoso');
    expect(text()).toContain('TXN-123');
    expect(labels()).toEqual([]);
    expect(document.activeElement).toBe(element.querySelector('h1'));
  });

  it.each([
    ['FAILED', 'No se pudo completar'],
    ['EXPIRED', 'venció'],
  ] as const)('en estado %s muestra el mensaje, sin referencia, con reintentar y volver', (status, message) => {
    setup();
    getPayment.mockReturnValue(
      of(paymentFixture({ status, status_label: 'Etiqueta', transaction_reference: null, actions: RETRY_ACTIONS })),
    );
    const { text, labels } = render();
    expect(text()).toContain(message);
    expect(text()).not.toContain('Referencia');
    expect(labels()).toEqual(['Reintentar', 'Volver']);
  });

  it('en estado terminal ofrece hacer otro pago y ver el historial', () => {
    setup();
    getPayment.mockReturnValue(
      of(paymentFixture({ status: 'FAILED', transaction_reference: null, actions: RETRY_ACTIONS })),
    );
    const { element } = render();
    const links = Array.from(element.querySelectorAll('nav a')).map((link) => link.getAttribute('href'));
    expect(links).toEqual(['/payments', '/payments/history']);
  });

  it('mientras está en proceso consulta de nuevo hasta el estado terminal y mantiene el pendiente', () => {
    vi.useFakeTimers();
    setup();
    getPayment
      .mockReturnValueOnce(of(paymentFixture({ status: 'PENDING', status_label: 'En proceso', transaction_reference: null })))
      .mockReturnValueOnce(of(paymentFixture({ status: 'PENDING', status_label: 'En proceso', transaction_reference: null })))
      .mockReturnValue(of(paymentFixture()));
    const { fixture, element, text } = render();
    expect(element.querySelector('h1')?.textContent).toBe('En proceso');
    expect(text()).toContain('Consultando el estado');
    vi.advanceTimersByTime(3000);
    fixture.detectChanges();
    expect(element.querySelector('h1')?.textContent).toBe('En proceso');
    vi.advanceTimersByTime(3000);
    fixture.detectChanges();
    expect(element.querySelector('h1')?.textContent).toBe('Pago exitoso');
    vi.advanceTimersByTime(30000);
    expect(getPayment).toHaveBeenCalledTimes(3);
  });

  it('reintentar crea un nuevo intento y navega a su resultado', () => {
    const { navigate } = setup();
    getPayment.mockReturnValue(of(paymentFixture({ status: 'FAILED', transaction_reference: null, actions: RETRY_ACTIONS })));
    retryPayment.mockReturnValue(of(paymentFixture({ payment_id: 'pay-2', status: 'PENDING' })));
    const { element } = render();
    element.querySelectorAll('button')[0].click();
    expect(retryPayment).toHaveBeenCalledWith('pay-1');
    expect(navigate).toHaveBeenCalledWith('/payments/result/pay-2');
  });

  it('si el reintento falla informa y permite intentarlo otra vez', () => {
    setup();
    getPayment.mockReturnValue(of(paymentFixture({ status: 'FAILED', transaction_reference: null, actions: RETRY_ACTIONS })));
    retryPayment.mockReturnValue(throwError(() => paymentError('network')));
    const { fixture, element, text } = render();
    element.querySelectorAll('button')[0].click();
    fixture.detectChanges();
    expect(text()).toContain('No pudimos crear el nuevo intento');
    expect(element.querySelectorAll('button')[0].disabled).toBe(false);
  });

  it('con error de consulta muestra el mensaje y "consultar de nuevo" reintenta', () => {
    setup();
    getPayment.mockReturnValueOnce(throwError(() => paymentError('network')));
    const { fixture, element, text, labels } = render();
    expect(text()).toContain('No pudimos consultar');
    expect(labels()).toEqual(['Consultar de nuevo', 'Volver']);
    getPayment.mockReturnValueOnce(of(paymentFixture()));
    element.querySelectorAll('button')[0].click();
    fixture.detectChanges();
    expect(element.querySelector('h1')?.textContent).toBe('Pago exitoso');
  });

  it('un pago inexistente muestra "no encontramos este pago"', () => {
    setup();
    getPayment.mockReturnValue(throwError(() => paymentError('not-found')));
    expect(render().text()).toContain('No encontramos este pago');
  });

  it('sin identificador en la ruta no consulta y muestra el error', () => {
    setup(null);
    expect(render().text()).toContain('No encontramos este pago');
    expect(getPayment).not.toHaveBeenCalled();
  });

  it('al cambiar el pago de la ruta consulta el nuevo', () => {
    const { params } = setup();
    getPayment.mockImplementation((id) => of(paymentFixture({ payment_id: id, transaction_reference: `REF-${id}` })));
    const { fixture, text } = render();
    params.next(convertToParamMap({ paymentId: 'pay-2' }));
    fixture.detectChanges();
    expect(text()).toContain('REF-pay-2');
  });
});
