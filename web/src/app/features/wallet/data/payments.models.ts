/** Contratos de la API de pagos (api/app/schemas.py). Tipos pequeños por caso de uso. */

export type RecipientId = 'contact-demo' | 'merchant-demo';

export type PaymentStatus = 'PENDING' | 'SUCCEEDED' | 'FAILED' | 'EXPIRED';

export type PaymentActionId = 'retry' | 'back' | 'view_previous';

export interface PaymentAction {
  readonly id: PaymentActionId;
  readonly label: string;
  readonly payment_id: string | null;
}

export interface ConfirmationRequest {
  readonly recipient: RecipientId | null;
  readonly amount_cents: number | null;
  readonly channel: string;
}

export interface Confirmation {
  readonly can_confirm: boolean;
  readonly intent_id: string | null;
  readonly recipient: string | null;
  readonly amount_cents: number | null;
  readonly reason: string | null;
  readonly message: string | null;
  readonly limit_cents: number | null;
  readonly actions: readonly PaymentAction[];
}

/** Intención de pago: el `intent_id` se reutiliza en cada repetición de la misma confirmación. */
export interface PaymentIntent {
  readonly intent_id: string;
  readonly amount_cents: number;
  readonly recipient: RecipientId;
  readonly channel: string;
}

export interface PaymentResult {
  readonly payment_id: string;
  readonly status: PaymentStatus;
  readonly status_label: string;
  readonly retry_of: string | null;
  /** Solo viene en pagos exitosos. */
  readonly transaction_reference: string | null;
  readonly actions: readonly PaymentAction[];
}

export interface PaymentHistoryItem extends PaymentResult {
  readonly amount_cents: number;
  readonly recipient: string;
  readonly created_at: string;
}
