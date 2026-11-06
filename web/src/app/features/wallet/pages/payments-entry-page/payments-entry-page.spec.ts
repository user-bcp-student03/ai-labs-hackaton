import { TestBed } from '@angular/core/testing';
import { PaymentsEntryPage } from './payments-entry-page';

describe('PaymentsEntryPage', () => {
  it('muestra el marcador de pagos de bajo monto', async () => {
    const fixture = TestBed.createComponent(PaymentsEntryPage);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('h1')?.textContent).toBe('Pagos de bajo monto');
    expect(element.querySelector('p')?.textContent).toContain('wallet está activa');
  });
});
