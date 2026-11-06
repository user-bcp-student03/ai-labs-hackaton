import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EXAMPLE_FLOW, onboardingAt } from '../../onboarding.fixtures';
import { StepIndicator } from './step-indicator';

describe('StepIndicator', () => {
  let fixture: ComponentFixture<StepIndicator>;

  async function render(completed: number) {
    fixture = TestBed.createComponent(StepIndicator);
    fixture.componentRef.setInput('steps', onboardingAt(EXAMPLE_FLOW, completed).steps);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('muestra todos los pasos en una lista ordenada con nombre accesible', async () => {
    const element = await render(0);
    expect(element.querySelector('nav')?.getAttribute('aria-label')).toBe('Progreso del registro');
    expect(element.querySelectorAll('ol > li')).toHaveLength(3);
  });

  it('marca solo el paso actual con aria-current="step" y dice "Paso n de m"', async () => {
    const element = await render(1);
    const current = element.querySelectorAll('li[aria-current="step"]');
    expect(current).toHaveLength(1);
    expect(current[0].textContent).toContain('Contacto (ejemplo no aprobado)');
    expect(element.querySelector('.indicator__summary')?.textContent).toBe('Paso 2 de 3: Contacto (ejemplo no aprobado)');
  });

  it('el estado de cada paso está en texto, no solo en color', async () => {
    const element = await render(1);
    const statuses = Array.from(element.querySelectorAll('.indicator__status')).map((node) => node.textContent?.trim());
    expect(statuses).toEqual(['(completado)', '(paso actual)', '(pendiente)']);
  });

  it('sin paso actual indica que todos están completos y no marca ninguno', async () => {
    const element = await render(3);
    expect(element.querySelectorAll('[aria-current]')).toHaveLength(0);
    expect(element.querySelector('.indicator__summary')?.textContent).toBe('Todos los pasos están completos.');
  });
});
