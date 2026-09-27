export const selectableModels = models => {
  const verified = models.filter(model => model.publisher_verified === true);
  const free = verified.filter(model => model.is_free);
  return free.length ? free : verified.slice(0, 1);
};

export const routingNotice = policy => {
  if (!policy) return 'Loading cost policy…';
  const limit = `${formatCost(policy.estimated_budget_usd)} estimated limit`;
  if (!policy.eligible_free_models) return `Paid only · No verified free model available · ${limit}`;
  return policy.paid_fallback_available ? `Free first · Cheapest verified paid fallback · ${limit}` : 'Verified free models only · No verified paid fallback available';
};

export const formatCost = value => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return 'unavailable';
  const number = Number(value);
  if (number > 0 && number < 0.00000001) return '< $0.00000001';
  return `$${number.toFixed(8).replace(/0+$/, '').replace(/\.$/, '')}`;
};