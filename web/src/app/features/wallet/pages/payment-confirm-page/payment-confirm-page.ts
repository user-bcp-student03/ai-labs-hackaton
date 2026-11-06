import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';
import { APP_ROUTES } from '../../../../core/config/app-config';
import { LiveAnnouncer } from '../../../../core/a11y/live-announcer';
import { PaymentError } from '../../data/payment-error';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentAction, PaymentIntent } from '../../data/payments.models';
import { PaymentActions } from '../../components/payment-actions/payment-actions';
import { formatCents, recipientLabel } from '../../rules/amount';
import { PaymentFlowStore } from '../../state/payment-flow.store';
import { PAYMENT_CHANNEL } from '../../wallet.config';
import { WALLET_COPY } from '../../wallet.copy';

interface Blocked {
  readonly message: string;
  readonly actions: readonly PaymentAction[];
}

const BACK_ACTION: PaymentAction = { id: 'back', label: WALLET_COPY.backButton, payment_id: null };

@Component({
  selector: 'app-payment-confirm-page',
  imports: [PaymentActions],
  templateUrl: './payment-confirm-page.html',
  styleUrl: './payment-confirm-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaymentConfirmPage implements OnDestroy {
  private readonly api = inject(PaymentsApiService);
  private readonly store = inject(PaymentFlowStore);
  private readonly router = inject(Router);
  private readonly announcer = inject(LiveAnnouncer);

  protected readonly copy = WALLET_COPY;
  protected readonly confirmation = this.store.confirmation;
  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);
  /** Rechazo definitivo al enviar (422/409): no se creó cobro. */
  private readonly rejected = signal<Blocked | null>(null);

  protected readonly blocked = computed<Blocked | null>(() => {
    const confirmation = this.confirmation();
    if (!confirmation || confirmation.can_confirm) return this.rejected();
    return {
      message: confirmation.message ?? this.copy.blockedFallback,
      actions: confirmation.actions.length > 0 ? confirmation.actions : [BACK_ACTION],
    };
  });

  protected readonly summary = computed(() => {
    const confirmation = this.confirmation();
    if (!confirmation) return null;
    return {
      recipient: recipientLabel(confirmation.recipient),
      amount: confirmation.amount_cents === null ? '' : formatCents(confirmation.amount_cents),
    };
  });

  /** Verdadero desde que se envía el pago: una vez enviado ya no corresponde registrar abandono. */
  private sent = false;
  private readonly heading = viewChild<ElementRef<HTMLElement>>('heading');

  constructor() {
    if (!this.store.confirmation()) {
      void this.router.navigateByUrl(APP_ROUTES.payments);
    }
    afterNextRender(() => this.heading()?.nativeElement.focus());
  }

  ngOnDestroy(): void {
    const intentId = this.store.confirmation()?.intent_id;
    if (!this.sent && intentId) {
      // Salida sin confirmar: se registra el abandono; un fallo de red no debe molestar a la persona.
      this.api.abandonConfirmation(intentId).subscribe({ error: () => undefined });
    }
    this.store.clear();
  }

  protected confirm(): void {
    const confirmation = this.confirmation();
    if (this.submitting() || !confirmation?.can_confirm) return;
    const intent = this.toIntent(confirmation.intent_id, confirmation.recipient, confirmation.amount_cents);
    if (!intent) return;
    this.submitting.set(true);
    this.submitError.set(null);
    this.sent = true;
    this.api.submitPayment(intent).subscribe({
      next: (result) => {
        this.store.clear();
        void this.router.navigateByUrl(APP_ROUTES.paymentResult(result.payment_id));
      },
      error: (error: PaymentError) => this.onSubmitError(error),
    });
  }

  protected back(): void {
    void this.router.navigateByUrl(APP_ROUTES.payments);
  }

  private toIntent(intentId: string | null, recipient: string | null, amount: number | null): PaymentIntent | null {
    if (!intentId || recipient === null || amount === null) return null;
    // El destino ya fue validado por la API al abrir la confirmación.
    return {
      intent_id: intentId,
      amount_cents: amount,
      recipient: recipient as PaymentIntent['recipient'],
      channel: PAYMENT_CHANNEL,
    };
  }

  private onSubmitError(error: PaymentError): void {
    this.submitting.set(false);
    if (error.kind === 'amount-exceeds-limit' || error.kind === 'previous-in-progress') {
      // Rechazo definitivo: no hubo cobro, así que sigue aplicando el registro de abandono.
      this.sent = false;
      const actions = error.actions.length > 0 ? error.actions : [BACK_ACTION];
      const message = error.message ?? this.copy.blockedFallback;
      this.rejected.set({ message, actions });
      this.announcer.announce(message);
      return;
    }
    // Sin respuesta clara el pago pudo enviarse: se conserva el mismo intent_id para repetir sin doble cobro.
    this.submitError.set(this.copy.submitFailed);
    this.announcer.announce(this.copy.submitFailed);
  }
}
