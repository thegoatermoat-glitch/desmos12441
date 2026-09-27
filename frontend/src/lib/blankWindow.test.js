import { insideBlankWindow, openBlankWindow } from './blankWindow';

afterEach(() => jest.restoreAllMocks());

test('opens the complete same-origin app without an opener', () => {
  const doc = document.implementation.createHTMLDocument('');
  const popup = { document: doc, closed: false, opener: window, focus: jest.fn(), close: jest.fn() };
  const opened = jest.spyOn(window, 'open').mockReturnValue(popup);
  expect(openBlankWindow('/notes')).toBe(true);
  expect(opened).toHaveBeenCalledWith('about:blank', '_blank');
  expect(popup.opener).toBe(null);
  const frame = doc.querySelector('[data-testid="about-blank-app-frame"]');
  expect(frame.src).toBe(new URL('/notes', window.location.origin).href);
  expect(doc.documentElement.dataset.calculatorWindow).toBe('true');
  expect(popup.focus).toHaveBeenCalled();
});

test('blocked windows return a safe result', () => {
  jest.spyOn(window, 'open').mockReturnValue(null);
  expect(openBlankWindow('/web')).toBe(false);
});

test('sandbox window-open exceptions are handled', () => {
  jest.spyOn(window, 'open').mockImplementation(() => { throw new Error('Blocked by browser'); });
  expect(openBlankWindow('/library')).toBe(false);
});

test('launcher cannot be used for a foreign origin', () => {
  const opened = jest.spyOn(window, 'open');
  expect(() => openBlankWindow('https://foreign.example/')).toThrow('Only app pages');
  expect(opened).not.toHaveBeenCalled();
  expect(insideBlankWindow()).toBe(false);
});