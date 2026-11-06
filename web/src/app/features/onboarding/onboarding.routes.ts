import { Routes } from '@angular/router';
import { ONBOARDING_COPY } from './onboarding.copy';
import { OnboardingPage } from './pages/onboarding-page/onboarding-page';
import { OnboardingStore } from './state/onboarding.store';

export const ONBOARDING_ROUTES: Routes = [
  {
    path: '',
    title: ONBOARDING_COPY.routeTitle,
    providers: [OnboardingStore],
    component: OnboardingPage,
  },
];
