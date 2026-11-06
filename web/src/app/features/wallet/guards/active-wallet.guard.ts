import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { APP_ROUTES } from '../../../core/config/app-config';
import { WalletApiService } from '../data/wallet-api.service';

/** Solo deja pasar con wallet activa; ante cualquier otro resultado (403, red, 503) redirige al onboarding. */
export const activeWalletGuard: CanActivateFn = () => {
  const router = inject(Router);
  const toOnboarding = router.createUrlTree([APP_ROUTES.onboarding]);
  return inject(WalletApiService)
    .checkPaymentsEntry()
    .pipe(
      map((entry) => (entry.allowed ? true : toOnboarding)),
      catchError(() => of(toOnboarding)),
    );
};
