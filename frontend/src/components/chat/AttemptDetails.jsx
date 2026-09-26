const labels = { answered: 'Answered', timeout: 'Timed out', empty_reply: 'No text returned', rate_limited: 'Rate limited',
  unavailable: 'Unavailable', account_error: 'Account issue', account_limit: 'Account limit', policy_error: 'Provider policy',
  request_error: 'Request rejected', network_error: 'Connection failed' };
export const AttemptDetails = ({ attempts }) => !attempts.length ? null : <details className="attempt-details" data-testid="chat-attempt-details">
  <summary data-testid="chat-attempt-details-toggle">{attempts.length} free model{attempts.length === 1 ? '' : 's'} tried</summary>
  <ol>{attempts.map((attempt, index) => <li key={`${attempt.model}-${index}`} data-testid={`chat-attempt-${index}`}><span>{attempt.model.split('/').pop().replace(':free', '')}</span><span>{labels[attempt.reason] || 'Unavailable'}</span></li>)}</ol>
</details>;