import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { APPROVED_FLOW_STATUS } from '../../data/onboarding.models';
import { ONBOARDING_COPY } from '../../onboarding.copy';

@Component({
  selector: 'app-flow-approval-notice',
  templateUrl: './flow-approval-notice.html',
  styleUrl: './flow-approval-notice.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FlowApprovalNotice {
  readonly approvalStatus = input.required<string>();
  readonly label = input<string | null | undefined>(null);

  protected readonly copy = ONBOARDING_COPY;
  protected readonly visible = computed(() => this.approvalStatus() !== APPROVED_FLOW_STATUS);
  protected readonly text = computed(() => this.label() || ONBOARDING_COPY.approvalNoticeFallback);
}
