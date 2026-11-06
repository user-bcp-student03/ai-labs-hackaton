import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { APP_CONFIG, DEFAULT_APP_CONFIG } from './core/config/app-config';
import { userIdentityInterceptor } from './core/http/user-identity.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([userIdentityInterceptor])),
    { provide: APP_CONFIG, useValue: DEFAULT_APP_CONFIG },
  ],
};
