import { TestBed } from '@angular/core/testing';
import { Observable, Subject, of, throwError } from 'rxjs';
import { LiveAnnouncer } from '../../../core/a11y/live-announcer';
import { ApiError, FieldError } from '../../../core/http/api-error';
import { OnboardingApiService } from '../data/onboarding-api.service';
import { FlowView, OnboardingView, StepValues } from '../data/onboarding.models';
import { ONBOARDING_COPY } from '../onboarding.copy';
import { ALTERNATE_FLOW, EXAMPLE_FLOW, completedOnboarding, onboardingAt } from '../onboarding.fixtures';
import { OnboardingStore } from './onboarding.store';

function apiError(kind: ApiError['kind'], fieldErrors: readonly FieldError[] = []): ApiError {
  return { kind, status: 0, code: null, fieldErrors, pendingStepIds: [], nextAction: null };
}

interface FakeApi {
  getFlow: ReturnType<typeof vi.fn<() => Observable<FlowView>>>;
  startOrResume: ReturnType<typeof vi.fn<() => Observable<OnboardingView>>>;
  getCurrent: ReturnType<typeof vi.fn<() => Observable<OnboardingView>>>;
  submitStep: ReturnType<typeof vi.fn<(id: string, step: string, values: StepValues) => Observable<OnboardingView>>>;
  close: ReturnType<typeof vi.fn<(id: string) => Observable<OnboardingView>>>;
}

function setup(flow: FlowView = EXAMPLE_FLOW, initial: OnboardingView = onboardingAt(flow, 0)) {
  const api: FakeApi = {
    getFlow: vi.fn(() => of(flow)),
    startOrResume: vi.fn(() => of(initial)),
    getCurrent: vi.fn(() => of(initial)),
    submitStep: vi.fn(() => of(initial)),
    close: vi.fn(() => of(completedOnboarding(flow))),
  };
  TestBed.configureTestingModule({
    providers: [OnboardingStore, { provide: OnboardingApiService, useValue: api }],
  });
  return { api, store: TestBed.inject(OnboardingStore), announcer: TestBed.inject(LiveAnnouncer) };
}

describe('OnboardingStore', () => {
  describe('load', () => {
    it('arma el estado desde la definición y el onboarding que devuelve la API', () => {
      const { store } = setup();
      store.load();
      expect(store.screen()).toBe('in-progress');
      expect(store.flow()?.flow_id).toBe('onboarding-ejemplo');
      expect(store.currentStep()?.id).toBe('datos-personales');
      expect(store.isLastStep()).toBe(false);
      expect(store.progressLabel()).toBe('Paso 1 de 3: Tus datos (ejemplo no aprobado)');
    });

    it('con otra definición el mismo store expone otros pasos', () => {
      const { store } = setup(ALTERNATE_FLOW);
      store.load();
      expect(store.currentStep()?.id).toBe('perfil');
      expect(store.isLastStep()).toBe(true);
    });

    it('queda en carga mientras la API no responde y anuncia el estado', () => {
      const { api, store, announcer } = setup();
      api.getFlow.mockReturnValue(new Subject<FlowView>());
      store.load();
      expect(store.screen()).toBe('loading');
      expect(announcer.message()).toBe(ONBOARDING_COPY.loading);
    });

    it('muestra el estado completado si el usuario ya terminó', () => {
      const { api, store, announcer } = setup();
      api.startOrResume.mockReturnValue(of(completedOnboarding(EXAMPLE_FLOW)));
      store.load();
      expect(store.screen()).toBe('completed');
      expect(announcer.message()).toBe(ONBOARDING_COPY.doneAnnouncement);
    });

    it('error de carga: pantalla de error con reintento posible', () => {
      const { api, store, announcer } = setup();
      api.getFlow.mockReturnValue(throwError(() => apiError('network')));
      store.load();
      expect(store.screen()).toBe('load-error');
      expect(announcer.message()).toBe(ONBOARDING_COPY.loadError);

      api.getFlow.mockReturnValue(of(EXAMPLE_FLOW));
      store.load();
      expect(store.screen()).toBe('in-progress');
    });

    it('flujo no configurado (503) tiene su propio estado', () => {
      const { api, store, announcer } = setup();
      api.getFlow.mockReturnValue(throwError(() => apiError('not-configured')));
      store.load();
      expect(store.screen()).toBe('not-configured');
      expect(announcer.message()).toBe(ONBOARDING_COPY.notConfigured);
    });

    it('si todos los pasos están completos pero el cierre no se confirmó, queda a la espera del cierre', () => {
      const pending = onboardingAt(EXAMPLE_FLOW, 3);
      const { store } = setup(EXAMPLE_FLOW, pending);
      store.load();
      expect(store.awaitingClose()).toBe(true);
      expect(store.currentStep()).toBeNull();
      expect(store.progressLabel()).toBe(ONBOARDING_COPY.allStepsDone);
    });
  });

  describe('submitCurrentStep', () => {
    it('envía el paso actual y avanza al siguiente, conservando la secuencia', () => {
      const { api, store, announcer } = setup();
      store.load();
      api.submitStep.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 1)));

      store.submitCurrentStep({ full_name: 'Ana Torres', document_number: 'TEST-12345' });

      expect(api.submitStep).toHaveBeenCalledWith('ob_test', 'datos-personales', {
        full_name: 'Ana Torres',
        document_number: 'TEST-12345',
      });
      expect(store.currentStep()?.id).toBe('contacto');
      expect(store.submitting()).toBe(false);
      expect(announcer.message()).toContain('Paso 2 de 3');
    });

    it('marca el último paso para cambiar la etiqueta del botón', () => {
      const { store } = setup(EXAMPLE_FLOW, onboardingAt(EXAMPLE_FLOW, 2));
      store.load();
      expect(store.isLastStep()).toBe(true);
    });

    it('tras el último paso cierra el onboarding y queda completado', () => {
      const { api, store, announcer } = setup(EXAMPLE_FLOW, onboardingAt(EXAMPLE_FLOW, 2));
      store.load();
      api.submitStep.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 3)));

      store.submitCurrentStep({ accept_terms: true });

      expect(api.close).toHaveBeenCalledWith('ob_test');
      expect(store.screen()).toBe('completed');
      expect(store.submitting()).toBe(false);
      expect(announcer.message()).toBe(ONBOARDING_COPY.doneAnnouncement);
    });

    it('si el cierre falla conserva el estado a la espera de cierre y muestra el mensaje con reintento', () => {
      const { api, store } = setup(EXAMPLE_FLOW, onboardingAt(EXAMPLE_FLOW, 2));
      store.load();
      api.submitStep.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 3)));
      api.close.mockReturnValue(throwError(() => apiError('network')));

      store.submitCurrentStep({ accept_terms: true });

      expect(store.awaitingClose()).toBe(true);
      expect(store.submitError()?.message).toBe(ONBOARDING_COPY.closeFailed);
      expect(store.submitting()).toBe(false);

      api.close.mockReturnValue(of(completedOnboarding(EXAMPLE_FLOW)));
      store.retryClose();
      expect(store.screen()).toBe('completed');
      expect(store.submitError()).toBeNull();
    });

    it('un 422 conserva el paso actual y expone los errores que envía el servidor', () => {
      const { api, store } = setup();
      store.load();
      const serverErrors = [{ field: 'full_name', rule: 'required', message: 'Escribe tu nombre completo.' }];
      api.submitStep.mockReturnValue(throwError(() => apiError('validation', serverErrors)));

      store.submitCurrentStep({ full_name: '', document_number: '' });

      expect(store.fieldErrors()).toEqual(serverErrors);
      expect(store.currentStep()?.id).toBe('datos-personales');
      expect(store.submitting()).toBe(false);
      expect(store.submitError()).toBeNull();
    });

    it('un reintento correcto limpia los errores de campo anteriores', () => {
      const { api, store } = setup();
      store.load();
      api.submitStep.mockReturnValue(
        throwError(() => apiError('validation', [{ field: 'full_name', rule: 'required', message: 'x' }])),
      );
      store.submitCurrentStep({});
      api.submitStep.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 1)));
      store.submitCurrentStep({ full_name: 'Ana Torres' });
      expect(store.fieldErrors()).toEqual([]);
    });

    it('un fallo de red muestra un mensaje de interfaz y no un error crudo', () => {
      const { api, store } = setup();
      store.load();
      api.submitStep.mockReturnValue(throwError(() => apiError('network')));
      store.submitCurrentStep({});
      expect(store.submitError()?.message).toBe(ONBOARDING_COPY.saveFailed);
      expect(store.submitting()).toBe(false);
    });

    it('un 409 (paso fuera de orden) resincroniza con la API y avisa', () => {
      const { api, store } = setup();
      store.load();
      api.submitStep.mockReturnValue(throwError(() => apiError('conflict')));
      api.startOrResume.mockReturnValue(of(onboardingAt(EXAMPLE_FLOW, 1)));

      store.submitCurrentStep({});

      expect(store.currentStep()?.id).toBe('contacto');
      expect(store.submitError()?.message).toBe(ONBOARDING_COPY.outOfSync);
      expect(store.submitting()).toBe(false);
    });

    it('un 409 cuya resincronización también falla muestra el mensaje de guardado', () => {
      const { api, store } = setup();
      store.load();
      api.submitStep.mockReturnValue(throwError(() => apiError('conflict')));
      api.startOrResume.mockReturnValue(throwError(() => apiError('network')));
      store.submitCurrentStep({});
      expect(store.submitError()?.message).toBe(ONBOARDING_COPY.saveFailed);
      expect(store.submitting()).toBe(false);
    });

    it('no envía dos veces mientras hay una solicitud en curso', () => {
      const { api, store } = setup();
      store.load();
      api.submitStep.mockReturnValue(new Subject<OnboardingView>());

      store.submitCurrentStep({ full_name: 'Ana' });
      store.submitCurrentStep({ full_name: 'Ana' });

      expect(api.submitStep).toHaveBeenCalledTimes(1);
      expect(store.submitting()).toBe(true);
    });

    it('no hace nada si todavía no hay onboarding cargado', () => {
      const { api, store } = setup();
      store.submitCurrentStep({});
      store.retryClose();
      expect(api.submitStep).not.toHaveBeenCalled();
      expect(api.close).not.toHaveBeenCalled();
    });
  });
});
