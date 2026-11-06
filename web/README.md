# wallet-web

Interfaz Angular de la HU-ONB (`user-onboarding-mvp-completion`). El formulario se construye con la definición de pasos que publica la API; el cliente no evalúa reglas, solo muestra los errores del servidor.

## Requisitos

- Node `^22.22.3 || ^24.15.0 || >=26` (requisito de `@angular/cli` 22.2.x); verificado con Node 26.9.0.
- La API de `api/` en `http://localhost:8000` con un flujo de pasos configurado (por ejemplo `ONB_STEPS_CONFIG_PATH=config/onboarding-steps.example.json`).

## Comandos

```
npm install
npm start          # ng serve con proxy /wallet-api -> http://localhost:8000
npm run lint       # ng lint (angular-eslint, reglas de accesibilidad de plantillas)
npm test           # ng test (Vitest); usar -- --watch=false para una sola corrida
npm run build      # ng build
```

Cobertura: `ng test --watch=false --coverage` requiere `@vitest/coverage-v8` (misma versión que `vitest`). No está en `package.json`; instalar solo para medir con `npm install --no-save @vitest/coverage-v8@<versión de vitest>`.

## Proxy e identidad de prueba

- `proxy.conf.json` reescribe `/wallet-api/*` hacia la API (sin CORS en la API).
- `src/app/core/config/app-config.ts` define `testUserId` (prefijo `TEST-`, ficticio y provisional hasta contar con `auth/`); el interceptor lo envía como `X-Payer-Id`. No hay pantalla de acceso ni se guarda nada en `localStorage`.

## Estructura

- `core/`: configuración, interceptor de identidad, traducción de errores HTTP y región `aria-live`.
- `features/onboarding/`: modelos, servicio HTTP, store (signals), componentes y páginas; textos en `onboarding.copy.ts` (provisionales).
- `features/wallet/`: servicio de wallet, guard de wallet activa y marcador de pagos de bajo monto.
