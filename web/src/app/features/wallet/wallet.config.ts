import { RecipientId } from './data/payments.models';

/** Configuración provisional del flujo de pago (OQ-15/OQ-16 abiertas): no inventar valores definitivos. */
export const PAYMENT_CHANNEL = 'web';

/** Moneda provisional para mostrar montos (cohorte MVP Perú). */
export const CURRENCY_SYMBOL = 'S/';

/** Frecuencia de consulta mientras el pago está en proceso. */
export const PAYMENT_POLL_INTERVAL_MS = 3000;

export interface RecipientOption {
  readonly id: RecipientId;
  readonly label: string;
}

/** Destinos permitidos por la API (lista cerrada en api/app/schemas.py). Etiquetas provisionales. */
export const RECIPIENT_OPTIONS: readonly RecipientOption[] = [
  { id: 'contact-demo', label: 'Contacto de prueba' },
  { id: 'merchant-demo', label: 'Comercio de prueba' },
];

/** Tope de monto aceptado por la API (centavos); el límite por canal lo valida el servidor. */
export const MAX_AMOUNT_CENTS = 100_000_000;
