import { Routes } from '@angular/router';
import { PaymentConfirmPage } from './pages/payment-confirm-page/payment-confirm-page';
import { PaymentHistoryPage } from './pages/payment-history-page/payment-history-page';
import { PAYMENT_ID_PARAM, PaymentResultPage } from './pages/payment-result-page/payment-result-page';
import { PaymentsEntryPage } from './pages/payments-entry-page/payments-entry-page';
import { WALLET_COPY } from './wallet.copy';

export const WALLET_ROUTES: Routes = [
  { path: '', title: WALLET_COPY.routeTitle, component: PaymentsEntryPage },
  { path: 'confirm', title: WALLET_COPY.confirmRouteTitle, component: PaymentConfirmPage },
  { path: `result/:${PAYMENT_ID_PARAM}`, title: WALLET_COPY.resultRouteTitle, component: PaymentResultPage },
  { path: 'history', title: WALLET_COPY.historyRouteTitle, component: PaymentHistoryPage },
];
