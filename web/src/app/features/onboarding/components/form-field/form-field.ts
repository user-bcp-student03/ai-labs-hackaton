import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { FieldValue, FieldView } from '../../data/onboarding.models';
import { ONBOARDING_COPY } from '../../onboarding.copy';

export function fieldInputId(fieldName: string): string {
  return `field-${fieldName}`;
}

@Component({
  selector: 'app-form-field',
  imports: [ReactiveFormsModule],
  templateUrl: './form-field.html',
  styleUrl: './form-field.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormField {
  readonly field = input.required<FieldView>();
  readonly control = input.required<FormControl<FieldValue>>();
  readonly error = input<string | null>(null);

  protected readonly copy = ONBOARDING_COPY;
  protected readonly inputId = computed(() => fieldInputId(this.field().name));
  protected readonly hintId = computed(() => `${this.inputId()}-hint`);
  protected readonly errorId = computed(() => `${this.inputId()}-error`);
  protected readonly labelText = computed(() => {
    const { label, required } = this.field();
    return required ? `${label}${ONBOARDING_COPY.requiredSuffix}` : label;
  });
  protected readonly describedBy = computed(() => {
    const ids = [this.field().hint ? this.hintId() : null, this.error() ? this.errorId() : null];
    const present = ids.filter((id): id is string => id !== null);
    return present.length > 0 ? present.join(' ') : null;
  });
}
