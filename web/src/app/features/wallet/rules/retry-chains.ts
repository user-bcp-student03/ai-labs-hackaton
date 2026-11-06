import { PaymentResult } from '../data/payments.models';

export interface HistoryEntry<T extends PaymentResult> {
  readonly item: T;
  readonly attempts: number;
}

/** Un reintento es un intento nuevo vinculado (OQ-02); en el historial cada cadena se muestra una sola vez, con su último intento. */
export function collapseRetryChains<T extends PaymentResult>(items: readonly T[]): readonly HistoryEntry<T>[] {
  const byId = new Map(items.map((item) => [item.payment_id, item]));
  const superseded = new Set(items.map((item) => item.retry_of).filter((id): id is string => id !== null));
  return items
    .filter((item) => !superseded.has(item.payment_id))
    .map((item) => ({ item, attempts: countAttempts(item, byId) }));
}

function countAttempts(latest: PaymentResult, byId: ReadonlyMap<string, PaymentResult>): number {
  let attempts = 1;
  let previousId = latest.retry_of;
  while (previousId !== null) {
    attempts += 1;
    previousId = byId.get(previousId)?.retry_of ?? null;
  }
  return attempts;
}

