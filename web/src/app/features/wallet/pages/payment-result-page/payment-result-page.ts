import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterRenderEffect,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { BehaviorSubject, EMPTY, Observable, combineLatest, interval, map, of, startWith, switchMap, takeWhile } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { APP_ROUTES } from '../../../../core/config/app-config';
import { LiveAnnouncer } from '../../../../core/a11y/live-announcer';
import { PaymentActions } from '../../components/payment-actions/payment-actions';
import { PaymentError } from '../../data/payment-error';
import { PaymentsApiService } from '../../data/payments-api.service';
import { PaymentAction, PaymentResult } from '../../data/payments.models';
import { PAYMENT_POLL_INTERVAL_MS } from '../../wallet.config';
import { WALLET_COPY } from '../../wallet.copy';

export const PAYMENT_ID_PARAM = 'paymentId';

type Poll = { readonly payment: PaymentResult } | { readonly error: PaymentError };

@Component({
  selector: 'app-payment-result-page',
  imports: [PaymentActions, RouterLink],
  templateUrl: './payment-result-page.html',
  styleUrl: './payment-result-page.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaymentResultPage {
  private readonly api = inject(PaymentsApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly announcer = inject(LiveAnnouncer);
  private readonly reload$ = new BehaviorSubject<void>(undefined);

  protected readonly copy = WALLET_COPY;
  protected readonly routes = APP_ROUTES;
  protected readonly backActions: readonly PaymentAction[] = [
    { id: 'back', label: WALLET_COPY.backButton, payment_id: null },
  ];
  protected readonly payment = signal<PaymentResult | null>(null);
  protected readonly loadError = signal<string | null>(null);
  protected readonly retrying = signal(false);
  protected readonly retryError = signal<string | null>(null);
  protected readonly pending = computed(() => this.payment()?.status === 'PENDING');
  protected readonly statusMessage = computed(() => {
    const status = this.payment()?.status;
    return status ? this.copy.statusMessages[status] : '';
  });

  private readonly heading = viewChild<ElementRef<HTMLElement>>('heading');
  private lastFocusedKey: string | null = null;

  constructor() {
    combineLatest([this.route.paramMap, this.reload$])
      .pipe(
        map(([params]) => params.get(PAYMENT_ID_PARAM)),
        switchMap((id) => this.watch(id)),
        takeUntilDestroyed(inject(DestroyRef)),
      )
      .subscribe((poll) => this.onPoll(poll));

    // El foco pasa al encabezado cuando cambia el estado (por ejemplo de "en proceso" a terminal).
    afterRenderEffect(() => {
      const key = this.payment()?.status ?? (this.loadError() ? 'ERROR' : null);
      if (key === null || key === this.lastFocusedKey) return;
      this.lastFocusedKey = key;
      this.heading()?.nativeElement.focus();
    });
  }

  protected reload(): void {
    this.reload$.next();
  }

  protected retry(): void {
    const current = this.payment();
    if (!current || this.retrying()) return;
    this.retrying.set(true);
    this.retryError.set(null);
    this.api.retryPayment(current.payment_id).subscribe({
      next: (created) => {
        this.retrying.set(false);
        void this.router.navigateByUrl(APP_ROUTES.paymentResult(created.payment_id));
      },
      error: () => {
        this.retrying.set(false);
        this.retryError.set(this.copy.retryFailed);
        this.announcer.announce(this.copy.retryFailed);
      },
    });
  }

  /** Consulta el pago y sigue consultando mientras esté en proceso; se detiene en un estado terminal o error. */
  private watch(id: string | null): Observable<Poll> {
    this.payment.set(null);
    this.loadError.set(null);
    this.retryError.set(null);
    this.lastFocusedKey = null;
    if (!id) {
      this.loadError.set(this.copy.resultNotFound);
      return EMPTY;
    }
    return interval(PAYMENT_POLL_INTERVAL_MS).pipe(
      startWith(0),
      switchMap(() =>
        this.api.getPayment(id).pipe(
          map((payment): Poll => ({ payment })),
          catchError((error: PaymentError) => of<Poll>({ error })),
        ),
      ),
      takeWhile((poll) => 'payment' in poll && poll.payment.status === 'PENDING', true),
    );
  }

  private onPoll(poll: Poll): void {
    if ('error' in poll) {
      const message = poll.error.kind === 'not-found' ? this.copy.resultNotFound : this.copy.resultLoadFailed;
      this.loadError.set(message);
      this.announcer.announce(message);
      return;
    }
    this.payment.set(poll.payment);
    this.announcer.announce(`${poll.payment.status_label}. ${this.copy.statusMessages[poll.payment.status]}`);
  }
}
