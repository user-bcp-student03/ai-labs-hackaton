import { Confirmation, PaymentHistoryItem, PaymentResult } from './data/payments.models';

export function confirmationFixture(overrides: Partial<Confirmation> = {}): Confirmation {
  return {
    can_confirm: true,
    intent_id: 'intent-1',
    recipient: 'contact-demo',
    amount_cents: 1050,
    reason: null,
    message: null,
    limit_cents: null,
    actions: [],
    ...overrides,
  };
}

export function paymentFixture(overrides: Partial<PaymentResult> = {}): PaymentResult {
  return {
    payment_id: 'pay-1',
    status: 'SUCCEEDED',
    status_label: 'Pago exitoso',
    retry_of: null,
    transaction_reference: 'TXN-123',
    actions: [],
    ...overrides,
  };
}

export function historyItemFixture(overrides: Partial<PaymentHistoryItem> = {}): PaymentHistoryItem {
  return {
    ...paymentFixture(),
    amount_cents: 1050,
    recipient: 'contact-demo',
    created_at: '2026-11-06T10:00:00Z',
    ...overrides,
  };
}
