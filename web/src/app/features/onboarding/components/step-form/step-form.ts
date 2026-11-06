import { DOCUMENT } from '@angular/common';
import { ChangeDetectionStrategy, Component, afterRenderEffect, computed, inject, input, output, viewChild } from '@angular/core';
import { FormControl, FormRecord, ReactiveFormsModule } from '@angular/forms';
import { FieldError } from '../../../../core/http/api-error';
import { FieldValue, StepValues, StepView } from '../../data/onboarding.models';
import { ONBOARDING_COPY } from '../../onboarding.copy';
import { SubmitError } from '../../state/onboarding.store';
import { ErrorSummary, ErrorSummaryItem } from '../error-summary/error-summary';
import { FormField, fieldInputId } from '../form-field/form-field';

type StepFormModel = FormRecord<FormControl<FieldValue>>;

/** Construye el formulario desde la definición del paso; no agrega validadores (el servidor valida, D-6). */
function buildStepForm(step: StepView): StepFormModel {
  const controls = Object.fromEntries(
    step.fields.map((field) => [
      field.name,
      new FormControl<FieldValue>(field.type === 'checkbox' ? false : '', { nonNullable: true }),
    ]),
  );
  return new FormRecord<FormControl<FieldValue>>(controls);
}

@Component({
  selector: 'app-step-form',
  imports: [ReactiveFormsModule, FormField, ErrorSummary],
  templateUrl: './step-form.html',
  styleUrl: './step-form.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepForm {
  readonly step = input.required<StepView>();
  readonly fieldErrors = input<readonly FieldError[]>([]);
  readonly submitError = input<SubmitError | null>(null);
  readonly submitting = input(false);
  readonly isLastStep = input(false);
  readonly stepSubmitted = output<StepValues>();

  private readonly document = inject(DOCUMENT);
  private readonly summary = viewChild(ErrorSummary);

  protected readonly form = computed(() => buildStepForm(this.step()));
  protected readonly fields = computed(() =>
    this.step().fields.map((field) => ({ field, control: this.form().controls[field.name] })),
  );
  protected readonly errorByField = computed(() => {
    const messages = new Map<string, string>();
    for (const error of this.fieldErrors()) {
      if (!messages.has(error.field)) messages.set(error.field, error.message);
    }
    return messages;
  });
  protected readonly summaryItems = computed<readonly ErrorSummaryItem[]>(() => {
    const knownFields = new Set(this.step().fields.map((field) => field.name));
    const fieldErrors = this.fieldErrors();
    if (fieldErrors.length > 0) {
      return fieldErrors.map((error) => ({
        fieldName: knownFields.has(error.field) ? error.field : null,
        message: error.message,
      }));
    }
    const submitError = this.submitError();
    return submitError ? [{ fieldName: null, message: submitError.message }] : [];
  });
  protected readonly summaryHeading = computed(() =>
    this.fieldErrors().length > 0 ? ONBOARDING_COPY.validationSummaryHeading : ONBOARDING_COPY.saveErrorHeading,
  );
  protected readonly submitLabel = computed(() => {
    if (this.submitting()) return ONBOARDING_COPY.saving;
    return this.isLastStep() ? ONBOARDING_COPY.finish : ONBOARDING_COPY.continue;
  });

  constructor() {
    // Cada intento fallido produce una lista nueva: el foco vuelve al resumen aunque el texto no cambie.
    afterRenderEffect(() => {
      this.summaryItems();
      this.summary()?.focus();
    });
  }

  protected submit(): void {
    this.stepSubmitted.emit(this.form().getRawValue());
  }

  protected focusField(fieldName: string): void {
    this.document.getElementById(fieldInputId(fieldName))?.focus();
  }
}
