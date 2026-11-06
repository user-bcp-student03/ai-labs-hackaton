import { CURRENCY_SYMBOL, MAX_AMOUNT_CENTS, RECIPIENT_OPTIONS } from '../wallet.config';

export type AmountParseResult =
  | { readonly ok: true; readonly cents: number }
  | { readonly ok: false; readonly reason: 'empty' | 'format' | 'not-positive' | 'too-large' };

const AMOUNT_PATTERN = /^(\d{1,9})(?:[.,](\d{1,2}))?$/;
const CENTS_PER_UNIT = 100;

/** Convierte el texto escrito por la persona (ej. "10,50") a centavos enteros. */
export function parseAmountToCents(text: string): AmountParseResult {
  const trimmed = text.trim();
  if (trimmed === '') return { ok: false, reason: 'empty' };
  const match = AMOUNT_PATTERN.exec(trimmed);
  if (!match) return { ok: false, reason: 'format' };
  const cents = Number(match[1]) * CENTS_PER_UNIT + Number((match[2] ?? '').padEnd(2, '0'));
  if (cents <= 0) return { ok: false, reason: 'not-positive' };
  if (cents > MAX_AMOUNT_CENTS) return { ok: false, reason: 'too-large' };
  return { ok: true, cents };
}

export function formatCents(cents: number): string {
  return `${CURRENCY_SYMBOL} ${(cents / CENTS_PER_UNIT).toFixed(2)}`;
}

export function recipientLabel(id: string | null): string {
  return RECIPIENT_OPTIONS.find((option) => option.id === id)?.label ?? id ?? '';
}
