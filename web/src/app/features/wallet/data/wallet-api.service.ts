import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PATHS, APP_CONFIG } from '../../../core/config/app-config';
import { mapApiError } from '../../../core/http/api-error';

export interface WalletView {
  readonly status: string;
  readonly activated_at: string | null;
}

export interface PaymentsEntryView {
  readonly allowed: boolean;
}

@Injectable({ providedIn: 'root' })
export class WalletApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(APP_CONFIG).apiBaseUrl;

  getWallet(): Observable<WalletView> {
    return this.http.get<WalletView>(`${this.baseUrl}${API_PATHS.wallet}`).pipe(mapApiError());
  }

  /** Responde 200 con wallet `activo`; con otro estado la API responde 403 `WALLET_NOT_ACTIVE`. */
  checkPaymentsEntry(): Observable<PaymentsEntryView> {
    return this.http.get<PaymentsEntryView>(`${this.baseUrl}${API_PATHS.paymentsEntry}`).pipe(mapApiError());
  }
}
