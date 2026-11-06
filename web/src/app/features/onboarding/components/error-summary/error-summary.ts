import { ChangeDetectionStrategy, Component, ElementRef, input, output, viewChild } from '@angular/core';
import { fieldInputId } from '../form-field/form-field';

export interface ErrorSummaryItem {
  /** Campo al que apunta el enlace; `null` cuando el mensaje no pertenece a un campo. */
  readonly fieldName: string | null;
  readonly message: string;
}

@Component({
  selector: 'app-error-summary',
  templateUrl: './error-summary.html',
  styleUrl: './error-summary.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ErrorSummary {
  readonly heading = input.required<string>();
  readonly items = input.required<readonly ErrorSummaryItem[]>();
  readonly fieldSelected = output<string>();

  protected readonly inputId = fieldInputId;
  private readonly container = viewChild.required<ElementRef<HTMLElement>>('container');

  focus(): void {
    this.container().nativeElement.focus();
  }

  protected select(event: Event, fieldName: string): void {
    event.preventDefault();
    this.fieldSelected.emit(fieldName);
  }
}
