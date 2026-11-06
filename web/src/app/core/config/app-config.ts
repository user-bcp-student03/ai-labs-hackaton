import { InjectionToken } from '@angular/core';

export interface AppConfig {
  readonly apiBaseUrl: string;
  readonly testUserId: string;
}

export const DEFAULT_APP_CONFIG: AppConfig = {
  // El proxy de desarrollo (proxy.conf.json) reescribe este prefijo hacia la API.
  apiBaseUrl: '/wallet-api',
  // Identidad ficticia provisional hasta contar con auth/ (decisión P-3).
  testUserId: 'TEST-user-0001',
};

export const APP_CONFIG = new InjectionToken<AppConfig>('APP_CONFIG');

export const PAYER_ID_HEADER = 'X-Payer-Id';

export const API_PATHS = {
  flow: '/onboarding/flow',
  onboarding: '/onboarding',
  currentOnboarding: '/onboarding/current',
  step: (onboardingId: string, stepId: string): string =>
    `/onboarding/${encodeURIComponent(onboardingId)}/steps/${encodeURIComponent(stepId)}`,
  close: (onboardingId: string): string => `/onboarding/${encodeURIComponent(onboardingId)}/close`,
  wallet: '/wallet',
  paymentsEntry: '/wallet/payments-entry',
  payments: '/payments',
  paymentConfirmations: '/payments/confirmations',
  paymentAbandon: (intentId: string): string => `/payments/confirmations/${encodeURIComponent(intentId)}/abandon`,
  payment: (paymentId: string): string => `/payments/${encodeURIComponent(paymentId)}`,
  paymentRetries: (paymentId: string): string => `/payments/${encodeURIComponent(paymentId)}/retries`,
} as const;

export const APP_ROUTES = {
  onboarding: '/onboarding',
  payments: '/payments',
  paymentConfirm: '/payments/confirm',
  paymentHistory: '/payments/history',
  paymentResult: (paymentId: string): string => `/payments/result/${encodeURIComponent(paymentId)}`,
} as const;
