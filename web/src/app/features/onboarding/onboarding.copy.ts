/**
 * Textos de interfaz del onboarding. Provisionales: no son textos regulatorios ni definitivos (OQ-16).
 * Los textos de pasos, campos y reglas vienen de la API.
 */
export const ONBOARDING_COPY = {
  routeTitle: 'Registro - Wallet',
  pageTitle: 'Completa tu registro',
  loading: 'Cargando tu registro…',
  loadError: 'No pudimos cargar tu registro. Revisa tu conexión y vuelve a intentarlo.',
  notConfigured: 'El registro no está disponible por ahora. Vuelve a intentarlo más tarde.',
  retryLoad: 'Reintentar',
  progressLabel: 'Progreso del registro',
  stepOf: (position: number, total: number, title: string): string => `Paso ${position} de ${total}: ${title}`,
  allStepsDone: 'Todos los pasos están completos.',
  stepStatus: {
    completed: 'completado',
    current: 'paso actual',
    pending: 'pendiente',
  },
  approvalNoticeTitle: 'Aviso',
  approvalNoticeFallback: 'Ejemplo no aprobado: estos pasos son solo para demostración y pruebas.',
  requiredSuffix: ' (obligatorio)',
  errorPrefix: 'Error:',
  validationSummaryHeading: 'Revisa estos datos para continuar',
  saveErrorHeading: 'No se pudo continuar',
  saveFailed: 'No pudimos guardar tus datos. Revisa tu conexión y vuelve a intentarlo.',
  outOfSync: 'Actualizamos tu registro para que continúes en el paso correcto.',
  closeFailed: 'No pudimos finalizar tu registro. Revisa tu conexión y vuelve a intentarlo.',
  continue: 'Continuar',
  finish: 'Finalizar registro',
  saving: 'Guardando…',
  retryClose: 'Reintentar finalización',
  stepsDoneNeedClose: 'Completaste todos los pasos. Finaliza tu registro para activar tu wallet.',
  stepSaved: 'Paso guardado.',
  doneAnnouncement: 'Registro finalizado. Tu wallet está activa.',
  doneHeading: 'Tu wallet está activa',
  doneMessage: 'Terminaste tu registro. Ya puedes ir a los pagos de bajo monto.',
  goToPayments: 'Ir a pagos',
} as const;
