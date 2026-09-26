import { ComputeEngine } from '@cortex-js/compute-engine';
import { convertLatexToMarkup, MathfieldElement } from 'mathlive';

MathfieldElement.fontsDirectory = '/mathlive/fonts';
MathfieldElement.soundsDirectory = null;
const engine = new ComputeEngine();
engine.precision = 15;

export function calculate(latex, mode, previous) {
  if (!latex.trim()) return { value: '', latex: '' };
  try {
    engine.angularUnit = mode.toLowerCase();
    const source = latex.replace(/\\operatorname\{(?:\\mathrm\{ans\}|ans)\}|\\mathrm\{ans\}|\bans\b/g, `(${previous || 0})`);
    const expr = engine.parse(source);
    if (!expr.isValid) return { error: 'Check your expression' };
    const result = expr.N();
    const value = result.valueOf();
    if (typeof value !== 'number' || !Number.isFinite(value)) return { error: 'Undefined or incomplete expression' };
    const formatted = Number(value.toPrecision(12)).toString();
    return { value: formatted, latex: engine.number(Number(formatted)).latex };
  } catch { return { error: 'Check your expression' }; }
}

export function mathMarkup(latex) {
  try { return convertLatexToMarkup(latex || ''); } catch { return ''; }
}