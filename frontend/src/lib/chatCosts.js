export const selectableModels = models => {
  const free = models.filter(model => model.is_free);
  return free.length ? free : models.slice(0, 1);
};

export const formatCost = value => {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return 'unavailable';
  const number = Number(value);
  if (number > 0 && number < 0.00000001) return '< $0.00000001';
  return `$${number.toFixed(8).replace(/0+$/, '').replace(/\.$/, '')}`;
};