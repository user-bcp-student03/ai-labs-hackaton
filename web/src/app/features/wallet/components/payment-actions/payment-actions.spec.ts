import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { PaymentAction } from '../../data/payments.models';
import { PaymentActions } from './payment-actions';

const ACTIONS: readonly PaymentAction[] = [
  { id: 'retry', label: 'Reintentar', payment_id: null },
  { id: 'view_previous', label: 'Ver estado del pago anterior', payment_id: 'pay-0' },
  { id: 'back', label: 'Volver', payment_id: null },
];

describe('PaymentActions', () => {
  function setup(busy = false) {
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(PaymentActions);
    fixture.componentRef.setInput('actions', ACTIONS);
    fixture.componentRef.setInput('busy', busy);
    const router = TestBed.inject(Router);
    const navigate = vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
    const retry = vi.fn();
    fixture.componentInstance.retry.subscribe(retry);
    fixture.detectChanges();
    const buttons = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button'));
    return { buttons, navigate, retry };
  }

  it('muestra una acción por botón con la etiqueta de la API', () => {
    expect(setup().buttons.map((button) => button.textContent?.trim())).toEqual([
      'Reintentar',
      'Ver estado del pago anterior',
      'Volver',
    ]);
  });

  it('reintentar emite el evento sin navegar', () => {
    const { buttons, navigate, retry } = setup();
    buttons[0].click();
    expect(retry).toHaveBeenCalledTimes(1);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('ver estado del pago anterior navega al resultado de ese pago', () => {
    const { buttons, navigate } = setup();
    buttons[1].click();
    expect(navigate).toHaveBeenCalledWith('/payments/result/pay-0');
  });

  it('volver navega a la entrada de pagos', () => {
    const { buttons, navigate } = setup();
    buttons[2].click();
    expect(navigate).toHaveBeenCalledWith('/payments');
  });

  it('deshabilita los botones mientras hay una solicitud en curso', () => {
    expect(setup(true).buttons.every((button) => button.disabled)).toBe(true);
  });
});
