import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { OnboardingDone } from './onboarding-done';

describe('OnboardingDone', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('muestra que la wallet está activa y enfoca el encabezado', async () => {
    const fixture = TestBed.createComponent(OnboardingDone);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    const heading = element.querySelector('h2') as HTMLElement;
    expect(heading.textContent).toBe('Tu wallet está activa');
    expect(document.activeElement).toBe(heading);
  });

  it('ofrece un enlace explícito a pagos, sin redirección automática', async () => {
    const fixture = TestBed.createComponent(OnboardingDone);
    await fixture.whenStable();
    const link = (fixture.nativeElement as HTMLElement).querySelector('a') as HTMLAnchorElement;
    expect(link.getAttribute('href')).toBe('/payments');
    expect(link.textContent).toBe('Ir a pagos');
  });
});
