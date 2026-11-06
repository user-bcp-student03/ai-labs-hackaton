import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FieldError } from '../../../../core/http/api-error';
import { StepValues, StepView } from '../../data/onboarding.models';
import { ALTERNATE_FLOW, EXAMPLE_FLOW } from '../../onboarding.fixtures';
import { StepForm } from './step-form';

const PERSONAL_STEP = EXAMPLE_FLOW.steps[0];
const TERMS_STEP = EXAMPLE_FLOW.steps[2];

describe('StepForm', () => {
  let fixture: ComponentFixture<StepForm>;
  let submitted: StepValues[];

  async function render(step: StepView, inputs: Record<string, unknown> = {}) {
    fixture = TestBed.createComponent(StepForm);
    submitted = [];
    fixture.componentInstance.stepSubmitted.subscribe((values) => submitted.push(values));
    fixture.componentRef.setInput('step', step);
    for (const [name, value] of Object.entries(inputs)) fixture.componentRef.setInput(name, value);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  function type(element: HTMLElement, id: string, value: string): void {
    const input = element.querySelector(`#${id}`) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  it('construye un control por cada campo de la definición', async () => {
    const element = await render(PERSONAL_STEP);
    expect(Array.from(element.querySelectorAll('input')).map((input) => input.id)).toEqual([
      'field-full_name',
      'field-document_number',
    ]);
  });

  it('con otra definición construye otros campos con el mismo componente', async () => {
    const element = await render(ALTERNATE_FLOW.steps[0]);
    expect(Array.from(element.querySelectorAll('input')).map((input) => `${input.id}:${input.type}`)).toEqual([
      'field-nickname:text',
      'field-newsletter:checkbox',
    ]);
  });

  it('emite los valores escritos: texto como cadena y casilla como booleano', async () => {
    const element = await render(TERMS_STEP);
    (element.querySelector('#field-accept_terms') as HTMLInputElement).click();
    element.querySelector('form')?.dispatchEvent(new Event('submit'));
    expect(submitted).toEqual([{ accept_terms: true }]);
  });

  it('emite texto tal cual y no valida en el cliente: un campo vacío también se envía', async () => {
    const element = await render(PERSONAL_STEP);
    type(element, 'field-full_name', 'Ana Torres');
    element.querySelector('form')?.dispatchEvent(new Event('submit'));
    expect(submitted).toEqual([{ full_name: 'Ana Torres', document_number: '' }]);
  });

  it('muestra el mensaje del servidor junto al campo y un resumen con enlaces', async () => {
    const errors: FieldError[] = [
      { field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' },
      { field: 'document_number', rule: 'pattern', message: 'Escribe el documento de prueba con el formato TEST-12345.' },
    ];
    const element = await render(PERSONAL_STEP, { fieldErrors: errors });
    expect(element.querySelector('#field-full_name-error')?.textContent).toContain('Escribe tu nombre completo.');
    expect(element.querySelector('#field-document_number-error')?.textContent).toContain('TEST-12345');
    expect(element.querySelector('app-error-summary h3')?.textContent).toBe('Revisa estos datos para continuar');
    expect(element.querySelectorAll('app-error-summary a')).toHaveLength(2);
  });

  it('mueve el foco al resumen de errores cuando llegan errores', async () => {
    const element = await render(PERSONAL_STEP);
    expect(element.querySelector('app-error-summary')).toBeNull();
    fixture.componentRef.setInput('fieldErrors', [{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }]);
    await fixture.whenStable();
    expect(document.activeElement).toBe(element.querySelector('app-error-summary section'));
  });

  it('vuelve a enfocar el resumen en un segundo intento fallido con los mismos errores', async () => {
    const element = await render(PERSONAL_STEP);
    const first = [{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }];
    fixture.componentRef.setInput('fieldErrors', first);
    await fixture.whenStable();
    (element.querySelector('#field-full_name') as HTMLInputElement).focus();
    fixture.componentRef.setInput('fieldErrors', [...first]);
    await fixture.whenStable();
    expect(document.activeElement).toBe(element.querySelector('app-error-summary section'));
  });

  it('conserva lo escrito después de un error (no obliga a reingresar)', async () => {
    const element = await render(PERSONAL_STEP);
    type(element, 'field-full_name', 'Ana Torres');
    fixture.componentRef.setInput('fieldErrors', [{ field: 'document_number', rule: 'required', message: 'Escribe el número de documento de prueba.' }]);
    await fixture.whenStable();
    expect((element.querySelector('#field-full_name') as HTMLInputElement).value).toBe('Ana Torres');
  });

  it('al elegir un error del resumen el foco va al campo', async () => {
    const element = await render(PERSONAL_STEP, {
      fieldErrors: [{ field: 'document_number', rule: 'required', message: 'Escribe el número de documento de prueba.' }],
    });
    (element.querySelector('app-error-summary a') as HTMLAnchorElement).click();
    expect(document.activeElement).toBe(element.querySelector('#field-document_number'));
  });

  it('un error de un campo desconocido aparece en el resumen sin enlace', async () => {
    const element = await render(PERSONAL_STEP, {
      fieldErrors: [{ field: 'otro', rule: 'unknown_field', message: 'Dato no esperado.' }],
    });
    expect(element.querySelector('app-error-summary a')).toBeNull();
    expect(element.querySelector('app-error-summary li')?.textContent).toContain('Dato no esperado.');
  });

  it('un error de guardado se muestra en el resumen con su propio encabezado', async () => {
    const element = await render(PERSONAL_STEP, { submitError: { message: 'No pudimos guardar tus datos.' } });
    expect(element.querySelector('app-error-summary h3')?.textContent).toBe('No se pudo continuar');
    expect(document.activeElement).toBe(element.querySelector('app-error-summary section'));
  });

  it('deshabilita el botón y cambia su texto mientras hay una solicitud en curso', async () => {
    const element = await render(PERSONAL_STEP, { submitting: true });
    const button = element.querySelector('button') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(button.textContent).toBe('Guardando…');
    expect(element.querySelector('form')?.getAttribute('aria-busy')).toBe('true');
  });

  it('el botón dice "Continuar" y en el último paso "Finalizar registro"', async () => {
    const middle = await render(PERSONAL_STEP);
    expect(middle.querySelector('button')?.textContent).toBe('Continuar');
    const last = await render(TERMS_STEP, { isLastStep: true });
    expect(last.querySelector('button')?.textContent).toBe('Finalizar registro');
  });
});
