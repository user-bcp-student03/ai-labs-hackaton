import { Injectable, signal } from '@angular/core';
import { Confirmation } from '../data/payments.models';

/** Confirmación abierta en curso (solo en memoria: no se guarda nada sensible en localStorage). */
@Injectable({ providedIn: 'root' })
export class PaymentFlowStore {
  private readonly current = signal<Confirmation | null>(null);
  readonly confirmation = this.current.asReadonly();

  open(confirmation: Confirmation): void {
    this.current.set(confirmation);
  }

  clear(): void {
    this.current.set(null);
  }
}
