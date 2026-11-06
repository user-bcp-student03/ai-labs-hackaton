import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LiveAnnouncer } from './core/a11y/live-announcer';
import { App } from './app';

describe('App', () => {
  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  it('tiene un único <main> enfocable, enlace de salto y una región aria-live', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelectorAll('main')).toHaveLength(1);
    expect(element.querySelector('a.skip-link')?.getAttribute('href')).toBe('#main-content');
    expect(element.querySelector('[aria-live="polite"]')).not.toBeNull();
  });

  it('el enlace de salto mueve el foco al contenido principal', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    (element.querySelector('a.skip-link') as HTMLAnchorElement).click();
    expect(document.activeElement).toBe(element.querySelector('main'));
  });

  it('la región aria-live refleja los anuncios', async () => {
    const fixture = TestBed.createComponent(App);
    TestBed.inject(LiveAnnouncer).announce('Paso guardado.');
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('[aria-live]')?.textContent).toBe('Paso guardado.');
  });
});
