import { RotateCcw } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

const shortName = model => model.name.replace(/^[^:]+:\s*/, '').replace(/\s*\(free\)\s*/gi, '').trim();
export const ModelPicker = ({ models, value, onChange, disabled, error, retry }) => {
  const selected = models.find(m => m.id === value);
  return <div className="model-controls" data-testid="chat-model-controls">
    <div className="model-select-row"><Select value={models.some(m => m.id === value) ? value : ''} onValueChange={onChange} disabled={disabled || !models.length}>
      <SelectTrigger className="free-model-select" data-testid="chat-model-select" aria-label="Free model"><SelectValue placeholder={error ? 'Models unavailable' : 'Loading models…'} /></SelectTrigger>
      <SelectContent data-testid="chat-model-menu">{models.map((m, index) => <SelectItem value={m.id} key={m.id} data-testid={`chat-model-option-${index}`}>{shortName(m)} · Free</SelectItem>)}</SelectContent>
    </Select><button type="button" className="icon-button" title="Refresh free models" data-testid="chat-model-refresh" disabled={disabled} onClick={retry}><RotateCcw size={14} /></button></div>
    <span className="model-policy" data-testid="chat-model-policy">{selected?.is_moderated === false ? 'No provider moderation listed; model rules still apply.' : 'Provider and model policies apply.'}</span>
  </div>;
};