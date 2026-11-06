import { Injectable, signal } from '@angular/core';

/** Mensaje de la región `aria-live` global (se renderiza una sola vez en el componente raíz). */
@Injectable({ providedIn: 'root' })
export class LiveAnnouncer {
  private readonly currentMessage = signal('');
  readonly message = this.currentMessage.asReadonly();

  announce(message: string): void {
    this.currentMessage.set(message);
  }
}
