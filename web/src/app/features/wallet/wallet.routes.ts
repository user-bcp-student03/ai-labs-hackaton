import { Routes } from '@angular/router';
import { PaymentsEntryPage } from './pages/payments-entry-page/payments-entry-page';
import { WALLET_COPY } from './wallet.copy';

export const WALLET_ROUTES: Routes = [{ path: '', title: WALLET_COPY.routeTitle, component: PaymentsEntryPage }];
