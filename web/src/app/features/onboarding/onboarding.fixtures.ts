import { FlowView, OnboardingView, StepStateView } from './data/onboarding.models';

/** Réplica de api/config/onboarding-steps.example.json tal como la publica GET /onboarding/flow. */
export const EXAMPLE_FLOW: FlowView = {
  flow_id: 'onboarding-ejemplo',
  approval_status: 'example_not_approved',
  label: 'Ejemplo no aprobado: estos pasos son solo para demostración y pruebas; no son requisitos de KYC ni regulatorios.',
  steps: [
    {
      id: 'datos-personales',
      order: 1,
      title: 'Tus datos (ejemplo no aprobado)',
      description: 'Completa tus datos para continuar.',
      fields: [
        { name: 'full_name', type: 'text', label: 'Nombre completo', required: true, max_length: 100, autocomplete: 'name', input_mode: 'text' },
        {
          name: 'document_number',
          type: 'text',
          label: 'Número de documento de prueba',
          hint: 'Formato de prueba: TEST- seguido de letras o números, por ejemplo TEST-12345.',
          required: true,
          max_length: 25,
          input_mode: 'text',
        },
      ],
    },
    {
      id: 'contacto',
      order: 2,
      title: 'Contacto (ejemplo no aprobado)',
      fields: [
        { name: 'phone', type: 'text', label: 'Celular', hint: '9 dígitos, sin espacios.', required: true, max_length: 9, autocomplete: 'tel-national', input_mode: 'tel' },
      ],
    },
    {
      id: 'aceptacion',
      order: 3,
      title: 'Confirmación (ejemplo no aprobado)',
      fields: [{ name: 'accept_terms', type: 'checkbox', label: 'Acepto los términos de ejemplo', required: true }],
    },
  ],
};

/** Otra definición, para demostrar que el mismo componente construye otros formularios. */
export const ALTERNATE_FLOW: FlowView = {
  flow_id: 'otro-flujo',
  approval_status: 'example_not_approved',
  label: 'Ejemplo no aprobado: flujo alterno.',
  steps: [
    {
      id: 'perfil',
      order: 1,
      title: 'Perfil alterno',
      fields: [
        { name: 'nickname', type: 'text', label: 'Apodo', required: false, max_length: 20 },
        { name: 'newsletter', type: 'checkbox', label: 'Quiero recibir novedades', required: false },
      ],
    },
  ],
};

export function onboardingAt(flow: FlowView, completed: number, overrides: Partial<OnboardingView> = {}): OnboardingView {
  const steps: StepStateView[] = flow.steps.map((step, index) => ({
    id: step.id,
    order: step.order,
    title: step.title,
    status: index < completed ? 'completed' : index === completed ? 'current' : 'pending',
  }));
  return {
    onboarding_id: 'ob_test',
    status: 'IN_PROGRESS',
    cohort: 'MVP-PE',
    wallet_status: 'pendiente',
    current_step_id: flow.steps[completed]?.id ?? null,
    steps,
    completed_steps: completed,
    total_steps: flow.steps.length,
    ...overrides,
  };
}

export function completedOnboarding(flow: FlowView): OnboardingView {
  return onboardingAt(flow, flow.steps.length, { status: 'COMPLETED', wallet_status: 'activo' });
}
