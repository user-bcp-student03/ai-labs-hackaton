import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { StepStateView } from '../../data/onboarding.models';
import { ONBOARDING_COPY } from '../../onboarding.copy';

@Component({
  selector: 'app-step-indicator',
  templateUrl: './step-indicator.html',
  styleUrl: './step-indicator.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepIndicator {
  readonly steps = input.required<readonly StepStateView[]>();

  protected readonly copy = ONBOARDING_COPY;
  protected readonly summary = computed(() => {
    const steps = this.steps();
    const position = steps.findIndex((step) => step.status === 'current');
    if (position < 0) return ONBOARDING_COPY.allStepsDone;
    return ONBOARDING_COPY.stepOf(position + 1, steps.length, steps[position].title);
  });
}
