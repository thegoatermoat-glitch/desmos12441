import { useEffect, useRef, useState, useMemo } from 'react';
import { Undo2, Redo2, Wrench } from 'lucide-react';
import { Keypad } from '../components/calculator/Keypad';
import { Settings } from '../components/calculator/Settings';
import { calculate, mathMarkup } from '../lib/calculator';
import { readStorage, writeStorage } from '../lib/api';

export default function Calculator() {
  const saved = useMemo(() => readStorage('calculator-state', { history: [], expression: '', mode: 'DEG', settings: {} }), []);
  const [history, setHistory] = useState(saved.history);
  const [expression, setExpression] = useState(saved.expression);
  const [mode, setMode] = useState(saved.mode);
  const [tab, setTab] = useState('main');
  const [settings, setSettings] = useState({ large: false, contrast: false, ...saved.settings });
  const [showSettings, setShowSettings] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const field = useRef(null), historyEnd = useRef(null), submitRef = useRef(null);
  const previous = history.length ? history[history.length - 1].value : '0';
  const result = useMemo(() => calculate(expression, mode, previous), [expression, mode, previous]);
  useEffect(() => {
    const mf = field.current;
    mf.mathVirtualKeyboardPolicy = 'manual';
    mf.smartFence = true;
    mf.defaultMode = 'math';
    mf.value = saved.expression;
    const onInput = () => { setExpression(mf.value); setSubmitted(false); };
    const onKey = (e) => { if (e.key === 'Enter') { e.preventDefault(); submitRef.current?.(); } };
    mf.addEventListener('input', onInput);
    mf.addEventListener('keydown', onKey);
    return () => { mf.removeEventListener('input', onInput); mf.removeEventListener('keydown', onKey); };
  }, [saved]);
  useEffect(() => { writeStorage('calculator-state', { history, expression, mode, settings }); }, [history, expression, mode, settings]);
  useEffect(() => { historyEnd.current?.scrollIntoView({ block: 'nearest' }); }, [history]);
  const insert = value => { field.current.focus(); field.current.insert(value, { insertionMode: 'replaceSelection', selectionMode: value.includes('#') ? 'placeholder' : 'after' }); setExpression(field.current.value); setSubmitted(false); };
  const command = name => { field.current.focus(); field.current.executeCommand(name); setExpression(field.current.value); };
  const submit = () => {
    if (!expression.trim()) return;
    setSubmitted(true);
    if (result.error) return;
    setHistory(items => [...items, { expression, ...result }].slice(-100));
    field.current.value = ''; setExpression(''); field.current.focus();
  };
  submitRef.current = submit;
  const clear = () => { setHistory([]); setExpression(''); field.current.value = ''; field.current.focus(); };
  return <main className="calculator-page" data-testid="calculator-page">
    <section className={`calculator ${settings.large ? 'large-type' : ''} ${settings.contrast ? 'high-contrast' : ''}`} aria-label="Scientific calculator" data-testid="calculator">
      <div className="expression-history" data-testid="calculator-history">
        {history.map((item, i) => <button className="history-line" data-testid={`history-expression-${i}`} key={i} title="Use this expression" onClick={() => { field.current.value = item.expression; setExpression(item.expression); field.current.focus(); }}>
          <span className="history-index">{i + 1}</span><span className="history-math" dangerouslySetInnerHTML={{ __html: mathMarkup(item.expression) }} /><span className="history-answer" data-testid={`history-result-${i}`}>{item.value}</span>
        </button>)}<div ref={historyEnd} />
      </div>
      <div className="expression-row" data-testid="calculator-expression-row">
        <math-field ref={field} data-testid="calculator-input" aria-label="Expression" virtual-keyboard-mode="off" />
        {expression && <output className={result.error ? 'live-result invalid' : 'live-result'} data-testid="calculator-result" aria-live="polite">{result.error ? (submitted ? result.error : '…') : result.value}</output>}
      </div>
      <div className="keypad-shell">
        <div className="calculator-toolbar">
          <div className="keypad-tabs" role="tablist" aria-label="Keypad">{['main', 'abc', 'func'].map(name => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'selected' : ''} data-testid={`keypad-tab-${name}`} onClick={() => setTab(name)}>{name}</button>)}</div>
          <div className="angle-toggle" data-testid="angle-mode-toggle">{['RAD', 'DEG'].map(m => <button key={m} aria-pressed={mode === m} className={mode === m ? 'selected' : ''} data-testid={`angle-mode-${m.toLowerCase()}`} onClick={() => setMode(m)}>{m}</button>)}</div>
          <button className="toolbar-icon" title="Undo" data-testid="calculator-undo" onMouseDown={e => e.preventDefault()} onClick={() => command('undo')}><Undo2 size={20} /></button>
          <button className="toolbar-icon" title="Redo" data-testid="calculator-redo" onMouseDown={e => e.preventDefault()} onClick={() => command('redo')}><Redo2 size={20} /></button>
          <button className="clear-all" disabled={!expression && !history.length} data-testid="calculator-clear-all" onClick={clear}>clear all</button>
          <button className="toolbar-icon settings-icon" title="Settings" data-testid="calculator-settings" onClick={() => setShowSettings(true)}><Wrench size={18} fill="currentColor" /></button>
        </div>
        <Keypad tab={tab} insert={insert} command={command} submit={submit} />
      </div>
    </section>
    <Settings open={showSettings} setOpen={setShowSettings} settings={settings} setSettings={setSettings} />
  </main>;
}