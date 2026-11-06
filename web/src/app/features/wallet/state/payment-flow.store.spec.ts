import { TestBed } from '@angular/core/testing';
import { Confirmation } from '../data/payments.models';
import { PaymentFlowStore } from './payment-flow.store';

const CONFIRMATION: Confirmation = {
  can_confirm: true,
  intent_id: 'i-1',
  recipient: 'contact-demo',
  amount_cents: 1050,
  reason: null,
  message: null,
  limit_cents: null,
  actions: [],
};

describe('PaymentFlowStore', () => {
  it('guarda y limpia la confirmación en curso', () => {
    const store = TestBed.inject(PaymentFlowStore);
    expect(store.confirmation()).toBeNull();
    store.open(CONFIRMATION);
    expect(store.confirmation()).toEqual(CONFIRMATION);
    store.clear();
    expect(store.confirmation()).toBeNull();
  });
});
