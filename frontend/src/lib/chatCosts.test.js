import { formatCost, selectableModels } from './chatCosts';

test('cost formatting does not label missing or tiny costs as free', () => {
  expect(formatCost(null)).toBe('unavailable');
  expect(formatCost(undefined)).toBe('unavailable');
  expect(formatCost('0.01')).toBe('$0.01');
  expect(formatCost('0')).toBe('$0');
  expect(formatCost('0.000000001')).toBe('< $0.00000001');
});

test('free choices remain preferred over paid choices', () => {
  const free = { id: 'free/model', is_free: true }, paid = { id: 'paid/model', is_free: false };
  expect(selectableModels([paid, free])).toEqual([free]);
  expect(selectableModels([paid])).toEqual([paid]);
});