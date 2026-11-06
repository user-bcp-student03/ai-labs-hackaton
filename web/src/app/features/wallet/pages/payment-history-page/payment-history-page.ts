import { ChangeDetectionStrategy, Component, ElementRef, afterNextRender, inject, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { APP_ROUTES } from '../../../../core/config/app-config';
import { LiveAnnouncer } from '../../../../core/a11y/live-announcer';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentHistoryItem } from '../../data/payments.models';
import { HistoryEntry, collapseRetryChains } from '../../rules/retry-chains';
import { formatCents, recipientLabel } from '../../rules/amount';
import { WALLET_COPY } from '../../wallet.copy';

@Component({
  selector: 'app-payment-history-page',
  imports: [RouterLink],
  templateUrl: './payment-history-page.html',
  styleUrl: './payment-history-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaymentHistoryPage {
  private readonly api = inject(PaymentsApiService);
  private readonly announcer = inject(LiveAnnouncer);

  protected readonly copy = WALLET_COPY;
  protected readonly paymentsRoute = APP_ROUTES.payments;
  protected readonly resultRoute = APP_ROUTES.paymentResult;
  protected readonly formatCents = formatCents;
  protected readonly recipientLabel = recipientLabel;
  protected readonly loading = signal(true);
  protected readonly failed = signal(false);
  protected readonly items = signal<readonly HistoryEntry<PaymentHistoryItem>[]>([]);

  private readonly heading = viewChild.required<ElementRef<HTMLElement>>('heading');

  constructor() {
    afterNextRender(() => this.heading().nativeElement.focus());
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.failed.set(false);
    this.api.listPayments().subscribe({
      next: (items) => {
        this.items.set(collapseRetryChains(items));
        this.loading.set(false);
      },
      error: () => {
        this.failed.set(true);
        this.loading.set(false);
        this.announcer.announce(this.copy.historyLoadFailed);
      },
    });
  }
}
