import { formatCost } from '../../lib/chatCosts';

export const ChatCost = ({ message, index }) => {
  if (message.is_paid === undefined) return null;
  const hasActual = message.actual_cost_usd !== null && message.actual_cost_usd !== undefined;
  const hasCharge = hasActual && Number(message.actual_cost_usd) > 0;
  const overBudget = hasActual && Number(message.actual_cost_usd) > Number(message.budget_usd);
  return <div className="message-cost" data-testid={`chat-message-cost-${index}`}>
    <span>{message.is_paid ? 'Paid response' : hasCharge ? 'Free-priced model' : 'Free response'}</span>
    {(message.is_paid || hasCharge) && <span data-testid={`chat-message-billing-${index}`}>{hasActual
      ? `Reported request cost: ${formatCost(message.actual_cost_usd)}`
      : `Estimated request cost: ${formatCost(message.estimated_cost_usd)} · Actual charge unavailable`}</span>}
    {overBudget && <span className="message-cost-warning" role="alert" data-testid={`chat-message-budget-warning-${index}`}>The provider-reported charge exceeds the estimate limit. Check your OpenRouter usage.</span>}
  </div>;
};