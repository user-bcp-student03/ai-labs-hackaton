export type FieldType = 'text' | 'checkbox';
export type StepStatus = 'completed' | 'current' | 'pending';
export type OnboardingStatus = 'IN_PROGRESS' | 'COMPLETED';
export type FieldValue = string | boolean;
export type StepValues = Readonly<Record<string, FieldValue>>;

export interface FieldView {
  readonly name: string;
  readonly type: FieldType;
  readonly label: string;
  readonly hint?: string | null;
  readonly required: boolean;
  readonly max_length?: number | null;
  readonly autocomplete?: string | null;
  readonly input_mode?: string | null;
}

export interface StepView {
  readonly id: string;
  readonly order: number;
  readonly title: string;
  readonly description?: string | null;
  readonly fields: readonly FieldView[];
}

export interface FlowView {
  readonly flow_id: string;
  readonly approval_status: string;
  readonly label?: string | null;
  readonly steps: readonly StepView[];
}

export interface StepStateView {
  readonly id: string;
  readonly order: number;
  readonly title: string;
  readonly status: StepStatus;
}

export interface OnboardingView {
  readonly onboarding_id: string;
  readonly status: OnboardingStatus;
  readonly cohort: string;
  readonly wallet_status: string;
  readonly current_step_id: string | null;
  readonly steps: readonly StepStateView[];
  readonly completed_steps: number;
  readonly total_steps: number;
}

export const APPROVED_FLOW_STATUS = 'approved';
