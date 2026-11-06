import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { Observable, Subject, of, throwError } from 'rxjs';
import { PaymentsApiService } from '../../data/payments-api.service';
import { Confirmation } from '../../data/payments.models';
import { PaymentFlowStore } from '../../state/payment-flow.store';
import { confirmationFixture } from '../../wallet.fixtures';
import { PaymentsEntryPage } from './payments-entry-page';

describe('PaymentsEntryPage', () => {
  const openConfirmation = vi.fn<(request: unknown) => Observable<Confirmation>>();

  function setup() {
    openConfirmation.mockReset();
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: PaymentsApiService, useValue: { openConfirmation } }],
    });
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    const fixture = TestBed.createComponent(PaymentsEntryPage);
    fixture.detectChanges();
    const element = fixture.nativeElement as HTMLElement;
    document.body.appendChild(element);
    const recipient = element.querySelector<HTMLSelectElement>('#recipient')!;
    const amount = element.querySelector<HTMLInputElement>('#amount')!;
    const fill = (recipientValue: string, amountValue: string) => {
      recipient.value = recipientValue;
      recipient.dispatchEvent(new Event('change'));
      amount.value = amountValue;
      amount.dispatchEvent(new Event('input'));
    };
    const submit = () => {
      element.querySelector('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, element, recipient, amount, fill, submit, navigate };
  }

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('muestra el formulario con etiquetas asociadas y el enlace al historial', () => {
    const { element } = setup();
    expect(element.querySelector('h1')?.textContent).toBe('Pagos de bajo monto');
    expect(element.querySelector('label[for="recipient"]')).not.toBeNull();
    expect(element.querySelector('label[for="amount"]')).not.toBeNull();
    expect(element.querySelector('a')?.getAttribute('href')).toBe('/payments/history');
  });

  it('con campos vacíos muestra errores junto a los campos, enfoca el primero y no llama a la API', () => {
    const { element, recipient, submit } = setup();
    submit();
    expect(element.querySelector('#recipient-error')?.textContent).toContain('Selecciona a quién');
    expect(element.querySelector('#amount-error')?.textContent).toContain('Escribe el monto');
    expect(recipient.getAttribute('aria-invalid')).toBe('true');
    expect(document.activeElement).toBe(recipient);
    expect(openConfirmation).not.toHaveBeenCalled();
  });

  it('con monto inválido enfoca el monto y explica qué corregir', () => {
    const { element, amount, fill, submit } = setup();
    fill('contact-demo', '10.555');
    submit();
    expect(element.querySelector('#amount-error')?.textContent).toContain('hasta 2 decimales');
    expect(document.activeElement).toBe(amount);
  });

  it('abre la confirmación con monto en centavos, guarda el resultado y navega', () => {
    const { fill, submit, navigate } = setup();
    const confirmation = confirmationFixture();
    openConfirmation.mockReturnValue(of(confirmation));
    fill('merchant-demo', '10,50');
    submit();
    expect(openConfirmation).toHaveBeenCalledWith({ recipient: 'merchant-demo', amount_cents: 1050, channel: 'web' });
    expect(TestBed.inject(PaymentFlowStore).confirmation()).toEqual(confirmation);
    expect(navigate).toHaveBeenCalledWith('/payments/confirm');
  });

  it('evita el doble envío mientras la solicitud está en curso', () => {
    const { element, fill, submit } = setup();
    openConfirmation.mockReturnValue(new Subject<Confirmation>());
    fill('contact-demo', '5');
    submit();
    submit();
    expect(openConfirmation).toHaveBeenCalledTimes(1);
    expect(element.querySelector('button[type="submit"]')?.hasAttribute('disabled')).toBe(true);
  });

  it('ante un fallo del servicio muestra un mensaje y permite reintentar', () => {
    const { element, fill, submit } = setup();
    openConfirmation.mockReturnValue(throwError(() => ({ kind: 'network' })));
    fill('contact-demo', '5');
    submit();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('No pudimos preparar tu pago');
    expect(element.querySelector('button[type="submit"]')?.hasAttribute('disabled')).toBe(false);
  });
});
