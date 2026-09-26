import { ArrowLeft, ArrowRight, Delete, CornerDownLeft } from 'lucide-react';

const main = [
  ['square', <i>a<sup>2</sup></i>, '#0^{2}'], ['power', <i>a<sup>b</sup></i>, '#0^{#?}'], ['absolute', <i>|a|</i>, '\\left|#0\\right|'],
  ['sqrt', '√', '\\sqrt{#0}'], ['root', <span><sup>n</sup>√</span>, '\\sqrt[#?]{#0}'], ['pi', 'π', '\\pi'],
  ['sin', 'sin', '\\sin(#0)'], ['cos', 'cos', '\\cos(#0)'], ['tan', 'tan', '\\tan(#0)'],
  ['open-paren', '(', '('], ['close-paren', ')', ')'], ['comma', ',', ','],
];
const functions = [
  ['asin', <span>sin<sup>−1</sup></span>, '\\arcsin(#0)'], ['acos', <span>cos<sup>−1</sup></span>, '\\arccos(#0)'], ['atan', <span>tan<sup>−1</sup></span>, '\\arctan(#0)'],
  ['log', 'log', '\\log_{10}(#0)'], ['ln', 'ln', '\\ln(#0)'], ['e', <i>e</i>, 'e'],
  ['factorial', <i>n!</i>, '#0!'], ['exp', <span>e<sup>x</sup></span>, 'e^{#?}'], ['ten-power', <span>10<sup>x</sup></span>, '10^{#?}'],
  ['floor', 'floor', '\\lfloor #0 \\rfloor'], ['ceil', 'ceil', '\\lceil #0 \\rceil'], ['inverse', <span>1/<i>a</i></span>, '\\frac{1}{#0}'],
];
const numbers = ['7', '8', '9', '÷', '4', '5', '6', '×', '1', '2', '3', '−', '0', '.', 'ans', '+'];
const alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');
export const Keypad = ({ tab, insert, command, submit }) => {
  const key = (id, label, value, extra = '') => <button key={id} className={`calc-key ${extra}`} data-testid={`calc-key-${id}`} aria-label={id} onMouseDown={e => e.preventDefault()} onClick={() => insert(value)}>{label}</button>;
  return <div className={`keypad-grid ${tab === 'abc' ? 'alphabet-mode' : ''}`} data-testid="calculator-keypad">
    {tab === 'abc' ? <div className="alphabet-keys">{alphabet.map(c => key(c, <i>{c}</i>, c))}{key('equals', '=', '=')}{key('abc-comma', ',', ',')}</div> : <>
      <div className="function-keys">{(tab === 'func' ? functions : main).map(([id, label, value]) => key(id, label, value))}</div>
      <div className="number-keys">{numbers.map(n => key(({ '÷': 'divide', '×': 'multiply', '−': 'minus', '+': 'plus', '.': 'decimal' })[n] || n, n, ({ '÷': '\\div', '×': '\\times', '−': '-', ans: '\\operatorname{ans}' })[n] || n, /^\d|\.$/.test(n) ? 'number-key' : ''))}</div>
    </>}
    <div className="utility-keys">
      {key('percent', '%', '\\%')}{key('fraction', <span className="fraction-label"><i>a</i><i>b</i></span>, '\\frac{#0}{#?}')}
      <button className="calc-key number-key" title="Move left" data-testid="calc-key-left" onMouseDown={e => e.preventDefault()} onClick={() => command('moveToPreviousChar')}><ArrowLeft size={17} /></button>
      <button className="calc-key number-key" title="Move right" data-testid="calc-key-right" onMouseDown={e => e.preventDefault()} onClick={() => command('moveToNextChar')}><ArrowRight size={17} /></button>
      <button className="calc-key backspace-key number-key" title="Backspace" data-testid="calc-key-backspace" onMouseDown={e => e.preventDefault()} onClick={() => command('deleteBackward')}><Delete size={17} /></button>
      <button className="calc-key enter-key" title="Enter" data-testid="calc-key-enter" onMouseDown={e => e.preventDefault()} onClick={submit}><CornerDownLeft size={23} /></button>
    </div>
  </div>;
};