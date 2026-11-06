import { TestBed } from '@angular/core/testing';
import { ErrorSummary, ErrorSummaryItem } from './error-summary';

async function render(items: readonly ErrorSummaryItem[]) {
  const fixture = TestBed.createComponent(ErrorSummary);
  fixture.componentRef.setInput('heading', 'Revisa estos datos para continuar');
  fixture.componentRef.setInput('items', items);
  await fixture.whenStable();
  return { fixture, element: fixture.nativeElement as HTMLElement };
}

describe('ErrorSummary', () => {
  it('muestra el encabezado y un enlace al campo por cada error con campo', async () => {
    const { element } = await render([
      { fieldName: 'full_name', message: 'Escribe tu nombre completo.' },
      { fieldName: 'phone', message: 'Escribe tu número de celular.' },
    ]);
    expect(element.querySelector('h3')?.textContent).toBe('Revisa estos datos para continuar');
    const links = Array.from(element.querySelectorAll('a'));
    expect(links.map((link) => link.getAttribute('href'))).toEqual(['#field-full_name', '#field-phone']);
    expect(links[0].textContent).toBe('Escribe tu nombre completo.');
  });

  it('un mensaje sin campo se muestra como texto sin enlace', async () => {
    const { element } = await render([{ fieldName: null, message: 'No pudimos guardar tus datos.' }]);
    expect(element.querySelector('a')).toBeNull();
    expect(element.querySelector('li')?.textContent).toContain('No pudimos guardar tus datos.');
  });

  it('el contenedor recibe el foco con focus()', async () => {
    const { fixture, element } = await render([{ fieldName: null, message: 'x' }]);
    document.body.appendChild(element);
    fixture.componentInstance.focus();
    expect(document.activeElement).toBe(element.querySelector('section'));
    element.remove();
  });

  it('al elegir un enlace emite el campo y no navega', async () => {
    const { fixture, element } = await render([{ fieldName: 'phone', message: 'Escribe tu número de celular.' }]);
    const selected: string[] = [];
    fixture.componentInstance.fieldSelected.subscribe((name) => selected.push(name));
    const event = new MouseEvent('click', { bubbles: true, cancelable: true });
    (element.querySelector('a') as HTMLAnchorElement).dispatchEvent(event);
    expect(selected).toEqual(['phone']);
    expect(event.defaultPrevented).toBe(true);
  });
});
