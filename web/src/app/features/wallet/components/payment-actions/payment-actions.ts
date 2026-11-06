import { ChangeDetectionStrategy, Component, inject, input, output } from '@angular/core';
import { Router } from '@angular/router';
import { APP_ROUTES } from '../../../../core/config/app-config';
import { PaymentAction } from '../../data/payments.models';

/** Acciones siguientes que indica la API. `back` y `view_previous` navegan; `retry` lo resuelve quien la usa. */
@Component({
  selector: 'app-payment-actions',
  templateUrl: './payment-actions.html',
  styleUrl: './payment-actions.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaymentActions {
  private readonly router = inject(Router);

  readonly actions = input.required<readonly PaymentAction[]>();
  readonly busy = input(false);
  readonly retry = output<void>();

  protected select(action: PaymentAction): void {
    if (action.id === 'retry') {
      this.retry.emit();
      return;
    }
    const target =
      action.id === 'view_previous' && action.payment_id
        ? APP_ROUTES.paymentResult(action.payment_id)
        : APP_ROUTES.payments;
    void this.router.navigateByUrl(target);
  }
}
