import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PATHS, APP_CONFIG } from '../../../core/config/app-config';
import { mapPaymentError } from './payment-error';
import {
  Confirmation,
  ConfirmationRequest,
  PaymentHistoryItem,
  PaymentIntent,
  PaymentResult,
} from './payments.models';

/** Pagos del pagador. La identidad (X-Payer-Id) la agrega `userIdentityInterceptor`, la misma del onboarding. */
@Injectable({ providedIn: 'root' })
export class PaymentsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(APP_CONFIG).apiBaseUrl;

  openConfirmation(request: ConfirmationRequest): Observable<Confirmation> {
    return this.http
      .post<Confirmation>(`${this.baseUrl}${API_PATHS.paymentConfirmations}`, request)
      .pipe(mapPaymentError());
  }

  /** Registra el abandono de una confirmación; la respuesta es 204 sin cuerpo. */
  abandonConfirmation(intentId: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}${API_PATHS.paymentAbandon(intentId)}`, {}).pipe(mapPaymentError());
  }

  /** Envía la intención; repetir el mismo `intent_id` devuelve el resultado original (idempotencia). */
  submitPayment(intent: PaymentIntent): Observable<PaymentResult> {
    return this.http.post<PaymentResult>(`${this.baseUrl}${API_PATHS.payments}`, intent).pipe(mapPaymentError());
  }

  getPayment(paymentId: string): Observable<PaymentResult> {
    return this.http.get<PaymentResult>(`${this.baseUrl}${API_PATHS.payment(paymentId)}`).pipe(mapPaymentError());
  }

  retryPayment(paymentId: string): Observable<PaymentResult> {
    return this.http
      .post<PaymentResult>(`${this.baseUrl}${API_PATHS.paymentRetries(paymentId)}`, {})
      .pipe(mapPaymentError());
  }

  listPayments(): Observable<readonly PaymentHistoryItem[]> {
    return this.http.get<readonly PaymentHistoryItem[]>(`${this.baseUrl}${API_PATHS.payments}`).pipe(mapPaymentError());
  }
}
