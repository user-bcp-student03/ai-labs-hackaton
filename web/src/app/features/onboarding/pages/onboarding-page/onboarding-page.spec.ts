import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Observable, Subject, of, throwError } from 'rxjs';
import { ApiError } from '../../../../core/http/api-error';
import { OnboardingApiService } from '../../data/onboarding-api.service';
import { FlowView, OnboardingView, StepValues } from '../../data/onboarding.models';
import { EXAMPLE_FLOW, completedOnboarding, onboardingAt } from '../../onboarding.fixtures';
import { OnboardingStore } from '../../state/onboarding.store';
import { OnboardingPage } from './onboarding-page';

function apiError(kind: ApiError['kind'], fieldErrors: ApiError['fieldErrors'] = []): ApiError {
  return { kind, status: 0, code: null, fieldErrors, pendingStepIds: [], nextAction: null };
}

describe('OnboardingPage', () => {
  let fixture: ComponentFixture<OnboardingPage>;
  let element: HTMLElement;
  const api = {
    getFlow: vi.fn<() => Observable<FlowView>>(),
    startOrResume: vi.fn<() => Observable<OnboardingView>>(),
    getCurrent: vi.fn<() => Observable<OnboardingView>>(),
    submitStep: vi.fn<(id: string, step: string, values: StepValues) => Observable<OnboardingView>>(),
    close: vi.fn<(id: string) => Observable<OnboardingView>>(),
  };

  async function open(): Promise<void> {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), OnboardingStore, { provide: OnboardingApiService, useValue: api }],
    });
    fixture = TestBed.createComponent(OnboardingPage);
    element = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  }

  function type(id: string, value: string): void {
    const input = element.querySelector(`#${id}`) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  async function submit(): Promise<void> {
    element.querySelector('form')?.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  }

  beforeEach(() => {
    vi.resetAllMocks();
    api.getFlow.mockReturnValue(of(EXAMPLE_FLOW));
    api.startOrResume.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 0)));
    api.close.mockReturnValue(of(completedOnboarding(EXAMPLE_FLOW)));
  });

  it('muestra el estado de carga mientras espera a la API', async () => {
    api.getFlow.mockReturnValue(new Subject<FlowView>());
    await open();
    expect(element.querySelector('h1')?.textContent).toBe('Completa tu registro');
    expect(element.querySelector('[aria-busy="true"]')?.textContent).toContain('Cargando');
  });

  it('muestra el aviso de ejemplo, el indicador de pasos y el formulario del primer paso', async () => {
    await open();
    expect(element.querySelector('[role="note"]')?.textContent).toContain('Ejemplo no aprobado');
    expect(element.querySelectorAll('app-step-indicator li')).toHaveLength(3);
    expect(element.querySelector('app-step-indicator li[aria-current="step"]')?.textContent).toContain('Tus datos');
    expect(element.querySelector('h2')?.textContent).toBe('Tus datos (ejemplo no aprobado)');
    expect(element.querySelector('#field-full_name')).not.toBeNull();
  });

  it('error de carga: mensaje comprensible y botón para reintentar', async () => {
    api.getFlow.mockReturnValue(throwError(() => apiError('network')));
    await open();
    expect(element.textContent).toContain('No pudimos cargar tu registro');
    expect(element.textContent).not.toContain('HttpErrorResponse');
    api.getFlow.mockReturnValue(of(EXAMPLE_FLOW));
    (element.querySelector('button') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(element.querySelector('form')).not.toBeNull();
  });

  it('flujo no configurado (503): estado propio sin botón de reintento', async () => {
    api.getFlow.mockReturnValue(throwError(() => apiError('not-configured')));
    await open();
    expect(element.textContent).toContain('no está disponible por ahora');
    expect(element.querySelector('form')).toBeNull();
  });

  it('con validación del servidor se queda en el paso, muestra el mensaje y enfoca el resumen', async () => {
    await open();
    api.submitStep.mockReturnValue(
      throwError(() => apiError('validation', [{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }])),
    );
    await submit();
    expect(element.querySelector('#field-full_name-error')?.textContent).toContain('Escribe tu nombre completo.');
    expect(element.querySelector('app-step-indicator li[aria-current="step"]')?.textContent).toContain('Tus datos');
    expect(document.activeElement).toBe(element.querySelector('app-error-summary section'));
  });

  it('al avanzar muestra el paso nuevo, lo marca como actual y enfoca su encabezado', async () => {
    await open();
    type('field-full_name', 'Ana Torres');
    type('field-document_number', 'TEST-12345');
    api.submitStep.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 1)));
    await submit();
    expect(api.submitStep).toHaveBeenCalledWith('ob_test', 'datos-personales', {
      full_name: 'Ana Torres',
      document_number: 'TEST-12345',
    });
    const heading = element.querySelector('h2') as HTMLElement;
    expect(heading.textContent).toBe('Contacto (ejemplo no aprobado)');
    expect(element.querySelector('app-step-indicator li[aria-current="step"]')?.textContent).toContain('Contacto');
    expect(document.activeElement).toBe(heading);
  });

  it('el recorrido completo termina en la pantalla de finalización con la wallet activa', async () => {
    await open();
    api.submitStep.mockReturnValueOnce(of(onboardingAt(EXAMPLE_FLOW, 1)));
    await submit();
    api.submitStep.mockReturnValueOnce(of(onboardingAt(EXAMPLE_FLOW, 2)));
    await submit();
    expect(element.querySelector('button')?.textContent).toBe('Finalizar registro');
    api.submitStep.mockReturnValueOnce(of(onboardingAt(EXAMPLE_FLOW, 3)));
    await submit();
    expect(api.close).toHaveBeenCalledWith('ob_test');
    expect(element.querySelector('app-onboarding-done h2')?.textContent).toBe('Tu wallet está activa');
    expect(element.querySelector('form')).toBeNull();
  });

  it('un usuario que ya terminó ve directamente la pantalla de finalización', async () => {
    api.startOrResume.mockReturnValue(of(completedOnboarding(EXAMPLE_FLOW)));
    await open();
    expect(element.querySelector('app-onboarding-done')).not.toBeNull();
  });

  it('no permite doble envío: el botón queda deshabilitado mientras hay solicitud en curso', async () => {
    await open();
    api.submitStep.mockReturnValue(new Subject<OnboardingView>());
    await submit();
    const button = element.querySelector('form button') as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    await submit();
    expect(api.submitStep).toHaveBeenCalledTimes(1);
  });

  it('pasos completos sin cierre confirmado: explica qué falta y permite reintentar', async () => {
    api.startOrResume.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 3)));
    api.close.mockReturnValueOnce(throwError(() => apiError('network')));
    await open();
    expect(element.querySelector('app-step-indicator li[aria-current]')).toBeNull();
    expect(element.textContent).toContain('Finaliza tu registro');

    (element.querySelector('section button') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(element.querySelector('app-error-summary')?.textContent).toContain('No pudimos finalizar tu registro');
    expect(document.activeElement).toBe(element.querySelector('app-error-summary section'));

    (element.querySelector('section button') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(element.querySelector('app-onboarding-done')).not.toBeNull();
  });
});
