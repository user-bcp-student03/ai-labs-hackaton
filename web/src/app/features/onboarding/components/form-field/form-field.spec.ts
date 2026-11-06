import { TestBed } from '@angular/core/testing';
import { FormControl } from '@angular/forms';
import { FieldValue, FieldView } from '../../data/onboarding.models';
import { FormField } from './form-field';

const PHONE: FieldView = {
  name: 'phone',
  type: 'text',
  label: 'Celular',
  hint: '9 dígitos, sin espacios.',
  required: true,
  max_length: 9,
  autocomplete: 'tel-national',
  input_mode: 'tel',
};

async function render(field: FieldView, error: string | null = null, value: FieldValue = '') {
  const fixture = TestBed.createComponent(FormField);
  const control = new FormControl<FieldValue>(value, { nonNullable: true });
  fixture.componentRef.setInput('field', field);
  fixture.componentRef.setInput('control', control);
  fixture.componentRef.setInput('error', error);
  await fixture.whenStable();
  return { element: fixture.nativeElement as HTMLElement, control, fixture };
}

describe('FormField', () => {
  it('asocia la etiqueta al campo y marca "(obligatorio)" en texto', async () => {
    const { element } = await render(PHONE);
    const input = element.querySelector('input') as HTMLInputElement;
    const label = element.querySelector('label') as HTMLLabelElement;
    expect(label.htmlFor).toBe(input.id);
    expect(label.textContent).toBe('Celular (obligatorio)');
    expect(input.getAttribute('aria-required')).toBe('true');
  });

  it('un campo opcional no lleva el sufijo de obligatorio', async () => {
    const { element } = await render({ ...PHONE, required: false });
    expect(element.querySelector('label')?.textContent).toBe('Celular');
  });

  it('publica autocomplete, inputmode y maxlength de la definición', async () => {
    const { element } = await render(PHONE);
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.getAttribute('autocomplete')).toBe('tel-national');
    expect(input.getAttribute('inputmode')).toBe('tel');
    expect(input.getAttribute('maxlength')).toBe('9');
  });

  it('no escribe atributos cuando la definición no los trae', async () => {
    const { element } = await render({ name: 'x', type: 'text', label: 'X', required: false });
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.hasAttribute('autocomplete')).toBe(false);
    expect(input.hasAttribute('maxlength')).toBe(false);
    expect(input.hasAttribute('aria-describedby')).toBe(false);
  });

  it('la pista y el error se enlazan con aria-describedby y aria-invalid', async () => {
    const { element } = await render(PHONE, 'Escribe 9 dígitos que empiecen con 9; por ejemplo: 912345678.');
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(input.getAttribute('aria-describedby')).toBe('field-phone-hint field-phone-error');
    const error = element.querySelector('#field-phone-error') as HTMLElement;
    expect(error.textContent).toContain('Error:');
    expect(error.textContent).toContain('912345678');
  });

  it('sin error no hay aria-invalid ni mensaje', async () => {
    const { element } = await render(PHONE);
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.hasAttribute('aria-invalid')).toBe(false);
    expect(input.getAttribute('aria-describedby')).toBe('field-phone-hint');
    expect(element.querySelector('.field__error')).toBeNull();
  });

  it('refleja en el control lo que escribe el usuario', async () => {
    const { element, control } = await render(PHONE);
    const input = element.querySelector('input') as HTMLInputElement;
    input.value = '912345678';
    input.dispatchEvent(new Event('input'));
    expect(control.value).toBe('912345678');
  });

  it('un campo checkbox usa una casilla con su etiqueta asociada', async () => {
    const { element, control } = await render(
      { name: 'accept_terms', type: 'checkbox', label: 'Acepto los términos de ejemplo', required: true },
      null,
      false,
    );
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.type).toBe('checkbox');
    expect((element.querySelector('label') as HTMLLabelElement).htmlFor).toBe(input.id);
    input.click();
    expect(control.value).toBe(true);
  });

  it('un checkbox con pista y error también los enlaza', async () => {
    const { element } = await render(
      { name: 'accept_terms', type: 'checkbox', label: 'Acepto', hint: 'Lee los términos.', required: true },
      'Marca la casilla para aceptar los términos y continuar.',
      false,
    );
    const input = element.querySelector('input') as HTMLInputElement;
    expect(input.getAttribute('aria-describedby')).toBe('field-accept_terms-hint field-accept_terms-error');
    expect(element.querySelector('#field-accept_terms-hint')?.textContent).toBe('Lee los términos.');
  });
});
