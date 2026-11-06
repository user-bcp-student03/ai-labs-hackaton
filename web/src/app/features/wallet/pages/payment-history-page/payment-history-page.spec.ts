import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Observable, Subject, of, throwError } from 'rxjs';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentHistoryItem } from '../../data/payments.models';
import { historyItemFixture } from '../../wallet.fixtures';
import { PaymentHistoryPage } from './payment-history-page';

describe('PaymentHistoryPage', () => {
  const listPayments = vi.fn<() => Observable<readonly PaymentHistoryItem[]>>();

  function render() {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: PaymentsApiService, useValue: { listPayments } }],
    });
    const fixture = TestBed.createComponent(PaymentHistoryPage);
    const element = fixture.nativeElement as HTMLElement;
    document.body.appendChild(element);
    fixture.detectChanges();
    return { fixture, element };
  }

  beforeEach(() => listPayments.mockReset());

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('muestra el estado de carga', () => {
    listPayments.mockReturnValue(new Subject<readonly PaymentHistoryItem[]>());
    expect(render().element.querySelector('[role="status"]')?.textContent).toContain('Cargando');
  });

  it('muestra el estado vacío con la acción de hacer un pago', async () => {
    listPayments.mockReturnValue(of([]));
    const { fixture, element } = render();
    await fixture.whenStable();
    expect(element.textContent).toContain('Todavía no tienes pagos');
    expect(element.querySelector('a.button')?.getAttribute('href')).toBe('/payments');
    expect(document.activeElement).toBe(element.querySelector('h1'));
  });

  it('muestra la referencia solo en los pagos exitosos', () => {
    listPayments.mockReturnValue(
      of([
        historyItemFixture({ payment_id: 'ok', transaction_reference: 'TXN-OK' }),
        historyItemFixture({
          payment_id: 'bad',
          status: 'FAILED',
          status_label: 'Pago fallido',
          transaction_reference: null,
          recipient: 'merchant-demo',
        }),
      ]),
    );
    const { element } = render();
    const items = element.querySelectorAll('li');
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toContain('TXN-OK');
    expect(items[0].textContent).toContain('S/ 10.50');
    expect(items[1].textContent).toContain('Pago fallido');
    expect(items[1].textContent).toContain('Comercio de prueba');
    expect(items[1].textContent).not.toContain('Referencia');
    expect(items[1].querySelector('a')?.getAttribute('href')).toBe('/payments/result/bad');
  });

  it('ante un error muestra el mensaje y permite intentar de nuevo', () => {
    listPayments.mockReturnValueOnce(throwError(() => ({ kind: 'network' })));
    const { fixture, element } = render();
    expect(element.querySelector('[role="alert"]')?.textContent).toContain('No pudimos cargar');
    listPayments.mockReturnValueOnce(of([historyItemFixture()]));
    element.querySelector('button')!.click();
    fixture.detectChanges();
    expect(element.querySelectorAll('li')).toHaveLength(1);
  });
});
