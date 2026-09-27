import { formatCost, selectableModels, routingNotice } from './chatCosts';

test('cost formatting does not label missing or tiny costs as free', () => {
  expect(formatCost(null)).toBe('unavailable');
  expect(formatCost(undefined)).toBe('unavailable');
  expect(formatCost('0.01')).toBe('$0.01');
  expect(formatCost('0')).toBe('$0');
  expect(formatCost('0.000000001')).toBe('< $0.00000001');
});

test('free choices remain preferred over paid choices', () => {
  const free = { id: 'free/model', is_free: true, publisher_verified: true }, paid = { id: 'paid/model', is_free: false, publisher_verified: true };
  expect(selectableModels([paid, free])).toEqual([free]);
  expect(selectableModels([paid])).toEqual([paid]);
});

test('an unmoderated provider alone does not make a model selectable', () => {
  expect(selectableModels([{ id: 'ordinary/model', is_free: true, is_moderated: false }])).toEqual([]);
});

test('paid-only availability is explicit before sending', () => {
  const text = routingNotice({ eligible_free_models: 0, eligible_paid_models: 1, paid_fallback_available: true, estimated_budget_usd: '0.01' });
  expect(text).toContain('Paid only');
  expect(text).toContain('No verified free model available');
  expect(text).toContain('$0.01');
});

test('absence of an audited paid fallback is not advertised as available', () => {
  expect(routingNotice({ eligible_free_models: 1, eligible_paid_models: 0, paid_fallback_available: false, estimated_budget_usd: '0.01' })).toContain('No verified paid fallback available');
});