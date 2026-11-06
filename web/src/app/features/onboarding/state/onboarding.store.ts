import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { LiveAnnouncer } from '../../../core/a11y/live-announcer';
import { ApiError, FieldError } from '../../../core/http/api-error';
import { OnboardingApiService } from '../data/onboarding-api.service';
import { FlowView, OnboardingView, StepValues, StepView } from '../data/onboarding.models';
import { ONBOARDING_COPY } from '../onboarding.copy';

export type OnboardingScreen = 'loading' | 'load-error' | 'not-configured' | 'in-progress' | 'completed';

/** Objeto (no texto) para que un mismo mensaje repetido vuelva a notificar a la interfaz. */
export interface SubmitError {
  readonly message: string;
}

/**
 * Estado del onboarding. El servidor es autoritativo (D-6): aquí no se evalúan reglas, solo se
 * conserva lo que la API devuelve. Se provee a nivel de ruta para no conservar estado entre visitas.
 */
@Injectable()
export class OnboardingStore {
  private readonly api = inject(OnboardingApiService);
  private readonly announcer = inject(LiveAnnouncer);
  private readonly destroyRef = inject(DestroyRef);

  private readonly screenState = signal<OnboardingScreen>('loading');
  private readonly flowState = signal<FlowView | null>(null);
  private readonly onboardingState = signal<OnboardingView | null>(null);
  private readonly fieldErrorsState = signal<readonly FieldError[]>([]);
  private readonly submittingState = signal(false);
  private readonly submitErrorState = signal<SubmitError | null>(null);

  readonly screen = this.screenState.asReadonly();
  readonly flow = this.flowState.asReadonly();
  readonly onboarding = this.onboardingState.asReadonly();
  readonly fieldErrors = this.fieldErrorsState.asReadonly();
  readonly submitting = this.submittingState.asReadonly();
  readonly submitError = this.submitErrorState.asReadonly();

  readonly currentStep = computed<StepView | null>(() => {
    const currentId = this.onboardingState()?.current_step_id;
    if (!currentId) return null;
    return this.flowState()?.steps.find((step) => step.id === currentId) ?? null;
  });

  readonly isLastStep = computed(() => {
    const onboarding = this.onboardingState();
    return this.currentStep() !== null && onboarding !== null && onboarding.completed_steps === onboarding.total_steps - 1;
  });

  /** Todos los pasos están completos pero el cierre aún no se confirmó (p. ej. falló la red). */
  readonly awaitingClose = computed(() => {
    const onboarding = this.onboardingState();
    return this.screenState() === 'in-progress' && onboarding !== null && onboarding.current_step_id === null;
  });

  readonly progressLabel = computed(() => {
    const onboarding = this.onboardingState();
    const step = this.currentStep();
    if (!onboarding || !step) return ONBOARDING_COPY.allStepsDone;
    return ONBOARDING_COPY.stepOf(onboarding.completed_steps + 1, onboarding.total_steps, step.title);
  });

  load(): void {
    this.screenState.set('loading');
    this.announcer.announce(ONBOARDING_COPY.loading);
    forkJoin({ flow: this.api.getFlow(), onboarding: this.api.startOrResume() })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ flow, onboarding }) => {
          this.flowState.set(flow);
          this.applyOnboarding(onboarding);
          this.announcer.announce(this.screenState() === 'completed' ? ONBOARDING_COPY.doneAnnouncement : this.progressLabel());
        },
        error: (error: ApiError) => this.failLoading(error),
      });
  }

  submitCurrentStep(values: StepValues): void {
    const onboarding = this.onboardingState();
    const step = this.currentStep();
    if (!onboarding || !step || this.submittingState()) return;
    this.beginRequest();
    this.api
      .submitStep(onboarding.onboarding_id, step.id, values)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (updated) => this.onStepSaved(updated),
        error: (error: ApiError) => this.onSubmitFailed(error),
      });
  }

  /** Reintenta el cierre cuando todos los pasos ya están completos. */
  retryClose(): void {
    const onboarding = this.onboardingState();
    if (!onboarding || this.submittingState()) return;
    this.beginRequest();
    this.closeOnboarding(onboarding.onboarding_id);
  }

  private onStepSaved(updated: OnboardingView): void {
    this.applyOnboarding(updated);
    if (updated.current_step_id === null) {
      this.closeOnboarding(updated.onboarding_id);
      return;
    }
    this.submittingState.set(false);
    this.announcer.announce(`${ONBOARDING_COPY.stepSaved} ${this.progressLabel()}`);
  }

  private closeOnboarding(onboardingId: string): void {
    this.api
      .close(onboardingId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (closed) => {
          this.applyOnboarding(closed);
          this.submittingState.set(false);
          this.announcer.announce(ONBOARDING_COPY.doneAnnouncement);
        },
        error: () => {
          this.submittingState.set(false);
          this.submitErrorState.set({ message: ONBOARDING_COPY.closeFailed });
        },
      });
  }

  private onSubmitFailed(error: ApiError): void {
    if (error.kind === 'validation') {
      this.submittingState.set(false);
      this.fieldErrorsState.set(error.fieldErrors);
      return;
    }
    if (error.kind === 'conflict') {
      this.resyncAfterConflict();
      return;
    }
    this.submittingState.set(false);
    this.submitErrorState.set({ message: ONBOARDING_COPY.saveFailed });
  }

  private resyncAfterConflict(): void {
    this.api
      .startOrResume()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (onboarding) => {
          this.applyOnboarding(onboarding);
          this.submittingState.set(false);
          this.submitErrorState.set({ message: ONBOARDING_COPY.outOfSync });
        },
        error: () => {
          this.submittingState.set(false);
          this.submitErrorState.set({ message: ONBOARDING_COPY.saveFailed });
        },
      });
  }

  private applyOnboarding(onboarding: OnboardingView): void {
    this.onboardingState.set(onboarding);
    this.fieldErrorsState.set([]);
    this.submitErrorState.set(null);
    this.screenState.set(onboarding.status === 'COMPLETED' ? 'completed' : 'in-progress');
  }

  private beginRequest(): void {
    this.submittingState.set(true);
    this.fieldErrorsState.set([]);
    this.submitErrorState.set(null);
  }

  private failLoading(error: ApiError): void {
    const notConfigured = error.kind === 'not-configured';
    this.screenState.set(notConfigured ? 'not-configured' : 'load-error');
    this.announcer.announce(notConfigured ? ONBOARDING_COPY.notConfigured : ONBOARDING_COPY.loadError);
  }
}
