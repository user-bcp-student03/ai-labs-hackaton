import { ChangeDetectionStrategy, Component, ElementRef, OnInit, afterRenderEffect, computed, inject, viewChild } from '@angular/core';
import { ErrorSummary, ErrorSummaryItem } from '../../components/error-summary/error-summary';
import { FlowApprovalNotice } from '../../components/flow-approval-notice/flow-approval-notice';
import { StepForm } from '../../components/step-form/step-form';
import { StepIndicator } from '../../components/step-indicator/step-indicator';
import { ONBOARDING_COPY } from '../../onboarding.copy';
import { OnboardingStore } from '../../state/onboarding.store';
import { OnboardingDone } from '../onboarding-done/onboarding-done';

@Component({
  selector: 'app-onboarding-page',
  imports: [FlowApprovalNotice, StepIndicator, StepForm, ErrorSummary, OnboardingDone],
  templateUrl: './onboarding-page.html',
  styleUrl: './onboarding-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingPage implements OnInit {
  protected readonly store = inject(OnboardingStore);
  protected readonly copy = ONBOARDING_COPY;

  private readonly stepHeading = viewChild<ElementRef<HTMLElement>>('stepHeading');
  private readonly closeSummary = viewChild(ErrorSummary);
  private lastStepId: string | null = null;

  protected readonly closeErrorItems = computed<readonly ErrorSummaryItem[]>(() => {
    const error = this.store.submitError();
    return error ? [{ fieldName: null, message: error.message }] : [];
  });

  constructor() {
    // El foco pasa al encabezado del paso nuevo; la primera carga no roba el foco.
    afterRenderEffect(() => {
      const stepId = this.store.currentStep()?.id ?? null;
      const heading = this.stepHeading();
      if (stepId === null || heading === undefined || stepId === this.lastStepId) return;
      const isFirstStep = this.lastStepId === null;
      this.lastStepId = stepId;
      if (!isFirstStep) heading.nativeElement.focus();
    });
    afterRenderEffect(() => {
      this.closeErrorItems();
      this.closeSummary()?.focus();
    });
  }

  ngOnInit(): void {
    this.store.load();
  }
}
