import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_PATHS, APP_CONFIG } from '../../../core/config/app-config';
import { mapApiError } from '../../../core/http/api-error';
import { FlowView, OnboardingView, StepValues } from './onboarding.models';

@Injectable({ providedIn: 'root' })
export class OnboardingApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(APP_CONFIG).apiBaseUrl;

  getFlow(): Observable<FlowView> {
    return this.http.get<FlowView>(this.url(API_PATHS.flow)).pipe(mapApiError());
  }

  /** Crea el onboarding del usuario o devuelve el existente (201 o 200). */
  startOrResume(): Observable<OnboardingView> {
    return this.http.post<OnboardingView>(this.url(API_PATHS.onboarding), null).pipe(mapApiError());
  }

  getCurrent(): Observable<OnboardingView> {
    return this.http.get<OnboardingView>(this.url(API_PATHS.currentOnboarding)).pipe(mapApiError());
  }

  submitStep(onboardingId: string, stepId: string, values: StepValues): Observable<OnboardingView> {
    return this.http
      .put<OnboardingView>(this.url(API_PATHS.step(onboardingId, stepId)), { values })
      .pipe(mapApiError());
  }

  close(onboardingId: string): Observable<OnboardingView> {
    return this.http.post<OnboardingView>(this.url(API_PATHS.close(onboardingId)), null).pipe(mapApiError());
  }

  private url(path: string): string {
    return `${this.baseUrl}${path}`;
  }
}
