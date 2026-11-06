import { ChangeDetectionStrategy, Component, ElementRef, afterNextRender, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { APP_ROUTES } from '../../../../core/config/app-config';
import { ONBOARDING_COPY } from '../../onboarding.copy';

@Component({
  selector: 'app-onboarding-done',
  imports: [RouterLink],
  templateUrl: './onboarding-done.html',
  styleUrl: './onboarding-done.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingDone {
  protected readonly copy = ONBOARDING_COPY;
  protected readonly paymentsRoute = APP_ROUTES.payments;

  private readonly heading = viewChild.required<ElementRef<HTMLElement>>('heading');

  constructor() {
    afterNextRender(() => this.heading().nativeElement.focus());
  }
}
