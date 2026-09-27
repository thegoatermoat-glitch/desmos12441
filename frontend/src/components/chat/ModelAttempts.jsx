import { formatCost } from '../../lib/chatCosts';

const reasons = {
  answered: 'Answered', rate_limited: 'Rate limited', unavailable: 'Unavailable',
  timeout: 'Timed out', network_error: 'Connection failed', empty_reply: 'No answer returned',
  account_error: 'Account error', account_limit: 'Account limit reached',
  policy_error: 'Provider policy', request_error: 'Request rejected',
  free_limit: 'Free-tier quota reached',
};

export const ModelAttempts = ({ attempts = [], testId }) => {
  if (!attempts.length) return null;
  return <details className="model-attempts" data-testid={testId}>
    <summary data-testid={`${testId}-toggle`}>{attempts.length} model {attempts.length === 1 ? 'attempt' : 'attempts'}</summary>
    <ol data-testid={`${testId}-list`}>{attempts.map((attempt, index) => <li key={`${attempt.model}-${index}`} data-testid={`${testId}-${index}`}>
      <span data-testid={`${testId}-${index}-model`}>{attempt.model}<small className="attempt-billing" data-testid={`${testId}-${index}-billing`}>{attempt.is_paid ? `Paid · ${attempt.actual_cost_usd != null ? 'reported' : 'estimated'} ${formatCost(attempt.actual_cost_usd ?? attempt.estimated_cost_usd)}` : 'Free'}</small></span>
      <span className={attempt.reason === 'answered' ? 'attempt-answered' : ''} data-testid={`${testId}-${index}-status`}>{reasons[attempt.reason] || 'Unavailable'}</span>
    </li>)}</ol>
  </details>;
};