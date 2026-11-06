import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { APP_CONFIG, PAYER_ID_HEADER } from '../config/app-config';

export const userIdentityInterceptor: HttpInterceptorFn = (request, next) => {
  const { apiBaseUrl, testUserId } = inject(APP_CONFIG);
  if (!request.url.startsWith(apiBaseUrl)) {
    return next(request);
  }
  return next(request.clone({ setHeaders: { [PAYER_ID_HEADER]: testUserId } }));
};
