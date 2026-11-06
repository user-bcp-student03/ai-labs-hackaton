import { formatCents, parseAmountToCents, recipientLabel } from './amount';

describe('parseAmountToCents', () => {
  it.each([
    ['10', 1000],
    ['10.5', 1050],
    ['10,50', 1050],
    [' 0.01 ', 1],
  ])('convierte "%s" a %i centavos', (text, cents) => {
    expect(parseAmountToCents(text)).toEqual({ ok: true, cents });
  });

  it.each([
    ['', 'empty'],
    ['   ', 'empty'],
    ['abc', 'format'],
    ['10.555', 'format'],
    ['-5', 'format'],
    ['0', 'not-positive'],
    ['0.00', 'not-positive'],
    ['9999999', 'too-large'],
  ] as const)('rechaza "%s" por %s', (text, reason) => {
    expect(parseAmountToCents(text)).toEqual({ ok: false, reason });
  });
});

describe('formatCents y recipientLabel', () => {
  it('formatea centavos con símbolo y dos decimales', () => {
    expect(formatCents(1050)).toBe('S/ 10.50');
  });

  it('usa la etiqueta del destino y cae al id si es desconocido', () => {
    expect(recipientLabel('contact-demo')).toBe('Contacto de prueba');
    expect(recipientLabel('otro')).toBe('otro');
    expect(recipientLabel(null)).toBe('');
  });
});
