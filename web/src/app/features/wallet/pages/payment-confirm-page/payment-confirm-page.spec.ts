import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { Observable, Subject, of, throwError } from 'rxjs';
import { PaymentError } from '../../data/payment-error';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentIntent, PaymentResult } from '../../data/payments.models';
import { PaymentFlowStore } from '../../state/payment-flow.store';
import { confirmationFixture, paymentFixture } from '../../wallet.fixtures';
import { PaymentConfirmPage } from './payment-confirm-page';

function paymentError(overrides: Partial<PaymentError>): PaymentError {
  return {
    kind: 'unknown',
    status: 500,
    message: null,
    limitCents: null,
    previousPaymentId: null,
    actions: [],
    ...overrides,
  };
}

describe('PaymentConfirmPage', () => {
  const submitPayment = vi.fn<(intent: PaymentIntent) => Observable<PaymentResult>>();
  const abandonConfirmation = vi.fn<(intentId: string) => Observable<void>>();

  function configure() {
    submitPayment.mockReset();
    abandonConfirmation.mockReset();
    abandonConfirmation.mockReturnValue(of(undefined));
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: PaymentsApiService, useValue: { submitPayment, abandonConfirmation } }],
    });
    return vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
  }

  function setup(confirmation = confirmationFixture()) {
    const navigate = configure();
    TestBed.inject(PaymentFlowStore).open(confirmation);
    const fixture = TestBed.createComponent(PaymentConfirmPage);
    const element = fixture.nativeElement as HTMLElement;
    document.body.appendChild(element);
    fixture.detectChanges();
    const buttons = () => Array.from(element.querySelectorAll('button'));
    const labels = () => buttons().map((button) => button.textContent?.trim());
    return { fixture, element, buttons, labels, navigate };
  }

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('muestra destino y monto antes de confirmar y enfoca el encabezado', async () => {
    const { fixture, element } = setup();
    await fixture.whenStable();
    expect(element.querySelector('h1')?.textContent).toBe('Confirma tu pago');
    expect(element.querySelector('dl')?.textContent).toContain('Contacto de prueba');
    expect(element.querySelector('dl')?.textContent).toContain('S/ 10.50');
    expect(document.activeElement).toBe(element.querySelector('h1'));
  });

  it('confirmar envía el intent_id de la confirmación y navega al resultado sin registrar abandono', () => {
    const { buttons, navigate, fixture } = setup();
    submitPayment.mockReturnValue(of(paymentFixture({ payment_id: 'pay-9', status: 'PENDING' })));
    buttons()[0].click();
    expect(submitPayment).toHaveBeenCalledWith({
      intent_id: 'intent-1',
      amount_cents: 1050,
      recipient: 'contact-demo',
      channel: 'web',
    });
    expect(navigate).toHaveBeenCalledWith('/payments/result/pay-9');
    fixture.destroy();
    expect(abandonConfirmation).not.toHaveBeenCalled();
  });

  it('evita el doble envío mientras hay una solicitud en curso', () => {
    const { buttons, fixture } = setup();
    submitPayment.mockReturnValue(new Subject<PaymentResult>());
    buttons()[0].click();
    fixture.detectChanges();
    buttons()[0].click();
    expect(submitPayment).toHaveBeenCalledTimes(1);
    expect(buttons().every((button) => button.disabled)).toBe(true);
  });

  it('tras un fallo de red conserva el mismo intent_id al repetir y no registra abandono', () => {
    const { buttons, element, fixture } = setup();
    submitPayment.mockReturnValueOnce(throwError(() => paymentError({ kind: 'network', status: 0 })));
    buttons()[0].click();
    fixture.detectChanges();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('no se cobrará dos veces');
    submitPayment.mockReturnValueOnce(of(paymentFixture()));
    buttons()[0].click();
    expect(submitPayment.mock.calls.map(([intent]) => intent.intent_id)).toEqual(['intent-1', 'intent-1']);
    fixture.destroy();
    expect(abandonConfirmation).not.toHaveBeenCalled();
  });

  it('ante 422 muestra el mensaje con el límite, solo volver, y registra abandono al salir', () => {
    const { buttons, labels, element, fixture } = setup();
    submitPayment.mockReturnValue(
      throwError(() =>
        paymentError({ kind: 'amount-exceeds-limit', status: 422, message: 'El límite es S/ 50.00', limitCents: 5000 }),
      ),
    );
    buttons()[0].click();
    fixture.detectChanges();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('S/ 50.00');
    expect(labels()).toEqual(['Volver']);
    fixture.destroy();
    expect(abandonConfirmation).toHaveBeenCalledWith('intent-1');
  });

  it('ante 409 ofrece ver el estado del pago anterior y volver', () => {
    const { buttons, labels, element, fixture, navigate } = setup();
    submitPayment.mockReturnValue(
      throwError(() =>
        paymentError({
          kind: 'previous-in-progress',
          status: 409,
          message: 'Tu pago anterior sigue en proceso.',
          actions: [
            { id: 'view_previous', label: 'Ver estado del pago anterior', payment_id: 'pay-0' },
            { id: 'back', label: 'Volver', payment_id: null },
          ],
        }),
      ),
    );
    buttons()[0].click();
    fixture.detectChanges();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('sigue en proceso');
    expect(labels()).toEqual(['Ver estado del pago anterior', 'Volver']);
    buttons()[0].click();
    expect(navigate).toHaveBeenCalledWith('/payments/result/pay-0');
  });

  it('un rechazo sin mensaje ni acciones usa el texto y la acción por defecto', () => {
    const { buttons, labels, element, fixture } = setup();
    submitPayment.mockReturnValue(throwError(() => paymentError({ kind: 'previous-in-progress', status: 409 })));
    buttons()[0].click();
    fixture.detectChanges();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('No pudimos continuar');
    expect(labels()).toEqual(['Volver']);
  });

  it('si la API no permite confirmar muestra el motivo y solo volver, sin registrar abandono', () => {
    const { labels, element, fixture } = setup(
      confirmationFixture({ can_confirm: false, intent_id: null, message: 'Faltan datos del destino.', actions: [] }),
    );
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('Faltan datos');
    expect(labels()).toEqual(['Volver']);
    fixture.destroy();
    expect(abandonConfirmation).not.toHaveBeenCalled();
  });

  it('volver sin confirmar navega a la entrada y registra el abandono aunque el registro falle', () => {
    const { buttons, navigate, fixture } = setup();
    abandonConfirmation.mockReturnValue(throwError(() => paymentError({ kind: 'network', status: 0 })));
    buttons()[1].click();
    expect(navigate).toHaveBeenCalledWith('/payments');
    fixture.destroy();
    expect(abandonConfirmation).toHaveBeenCalledWith('intent-1');
  });

  it('sin confirmación en curso redirige a la entrada de pagos', () => {
    const navigate = configure();
    TestBed.createComponent(PaymentConfirmPage);
    expect(navigate).toHaveBeenCalledWith('/payments');
  });
});
