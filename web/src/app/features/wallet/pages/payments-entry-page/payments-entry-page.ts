import { ChangeDetectionStrategy, Component } from '@angular/core';
import { WALLET_COPY } from '../../wallet.copy';

@Component({
  selector: 'app-payments-entry-page',
  templateUrl: './payments-entry-page.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaymentsEntryPage {
  protected readonly copy = WALLET_COPY;
}
