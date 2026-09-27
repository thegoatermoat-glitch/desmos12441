import { RotateCcw } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { selectableModels, formatCost } from '../../lib/chatCosts';

const shortName = model => model.publisher_model_name || model.name.replace(/^[^:]+:\s*/, '').replace(/\s*\(free\)\s*/gi, '').trim();
export const ModelPicker = ({ models, value, onChange, disabled, error, retry }) => {
  const selected = models.find(m => m.id === value);
  const choices = selectableModels(models);
  return <div className="model-controls" data-testid="chat-model-controls">
    <div className="model-select-row"><Select value={choices.some(m => m.id === value) ? value : ''} onValueChange={onChange} disabled={disabled || !choices.length}>
      <SelectTrigger className="free-model-select" data-testid="chat-model-select" aria-label={choices.some(m => m.is_free) ? 'Preferred free model' : 'Automatic lowest-cost model'}><SelectValue placeholder={error ? 'Models unavailable' : 'Loading models…'} /></SelectTrigger>
      <SelectContent data-testid="chat-model-menu">{choices.map((m, index) => <SelectItem value={m.id} key={m.id} data-testid={`chat-model-option-${index}`}>{shortName(m)} · {m.is_free ? 'Free' : 'Paid · automatic cost routing'}</SelectItem>)}</SelectContent>
    </Select><button type="button" className="icon-button" title="Refresh eligible models" data-testid="chat-model-refresh" disabled={disabled} onClick={retry}><RotateCcw size={14} /></button></div>
    <span className="model-policy" data-testid="chat-model-policy">{selected?.publisher_verified ? `Publisher-described as ${selected.publisher_label} · Model policies still apply.` : 'Only publisher-verified uncensored or unrestricted models.'}</span>
    {selected?.publisher_verified && <a className="model-policy model-publisher-source" href={selected.publisher_url} target="_blank" rel="noopener noreferrer" title={selected.publisher_quote} data-testid="chat-model-publisher-source">Publisher model card</a>}
    {selected && !selected.is_free && <span className="model-policy" data-testid="chat-model-pricing">{formatCost(Number(selected.prompt_price) * 1000000)}/M input · {formatCost(Number(selected.completion_price) * 1000000)}/M output</span>}
  </div>;
};