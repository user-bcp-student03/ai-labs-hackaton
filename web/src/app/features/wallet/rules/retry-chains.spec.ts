import { paymentFixture } from '../wallet.fixtures';
import { collapseRetryChains } from './retry-chains';

describe('collapseRetryChains', () => {
  it('muestra una sola vez la cadena de reintentos, con su último intento y el total de intentos', () => {
    const items = [
      paymentFixture({ payment_id: 'c', retry_of: 'b', status: 'FAILED' }),
      paymentFixture({ payment_id: 'b', retry_of: 'a', status: 'FAILED' }),
      paymentFixture({ payment_id: 'a', retry_of: null, status: 'FAILED' }),
      paymentFixture({ payment_id: 'x', retry_of: null }),
    ];
    const entries = collapseRetryChains(items);
    expect(entries.map((entry) => [entry.item.payment_id, entry.attempts])).toEqual([
      ['c', 3],
      ['x', 1],
    ]);
  });

  it('cuenta un intento cuando el original no está en la lista', () => {
    const entries = collapseRetryChains([paymentFixture({ payment_id: 'b', retry_of: 'a' })]);
    expect(entries[0].attempts).toBe(2);
  });

  it('devuelve vacío sin pagos', () => {
    expect(collapseRetryChains([])).toEqual([]);
  });
});
