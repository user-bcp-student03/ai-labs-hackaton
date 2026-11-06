import { TestBed } from '@angular/core/testing';
import { FlowApprovalNotice } from './flow-approval-notice';

async function render(approvalStatus: string, label: string | null) {
  const fixture = TestBed.createComponent(FlowApprovalNotice);
  fixture.componentRef.setInput('approvalStatus', approvalStatus);
  fixture.componentRef.setInput('label', label);
  await fixture.whenStable();
  return fixture.nativeElement as HTMLElement;
}

describe('FlowApprovalNotice', () => {
  it('muestra el aviso «ejemplo no aprobado» con el texto de la API', async () => {
    const element = await render('example_not_approved', 'Ejemplo no aprobado: solo demostración.');
    const note = element.querySelector('[role="note"]');
    expect(note?.textContent).toContain('Aviso:');
    expect(note?.textContent).toContain('Ejemplo no aprobado: solo demostración.');
  });

  it('usa un texto provisional si la API no envía etiqueta', async () => {
    const element = await render('example_not_approved', null);
    expect(element.querySelector('[role="note"]')?.textContent).toContain('Ejemplo no aprobado');
  });

  it('no muestra nada cuando el flujo está aprobado', async () => {
    const element = await render('approved', null);
    expect(element.querySelector('[role="note"]')).toBeNull();
  });
});
