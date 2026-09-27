import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { GameArtwork, GAME_COVER_FALLBACK } from './GameArtwork';

let container, root;
beforeAll(() => { global.IS_REACT_ACT_ENVIRONMENT = true; });
beforeEach(() => { container = document.createElement('div'); document.body.appendChild(container); root = createRoot(container); });
afterEach(() => { act(() => root.unmount()); container.remove(); });
const draw = game => act(() => root.render(<GameArtwork game={game} />));
const error = () => act(() => container.querySelector('img').dispatchEvent(new Event('error')));

test('missing covers use the supplied image', () => {
  draw({ id: 'missing.html', title: 'Missing Cover' });
  expect(container.querySelector('img').getAttribute('src')).toBe(GAME_COVER_FALLBACK);
  expect(container.querySelector('.fallback-cover')).not.toBeNull();
});

test('working assigned covers remain unchanged', () => {
  draw({ id: 'covered.html', title: 'Covered', cover: '/covers/original.png' });
  expect(container.querySelector('img').getAttribute('src')).toBe('/covers/original.png');
  expect(container.querySelector('.fallback-cover')).toBeNull();
});

test('a broken assigned cover switches to the supplied image without an error loop', () => {
  draw({ id: 'broken.html', title: 'Broken', cover: '/covers/broken.png' });
  error();
  expect(container.querySelector('img').getAttribute('src')).toBe(GAME_COVER_FALLBACK);
  error();
  expect(container.querySelector('img')).toBeNull();
  expect(container.querySelector('[data-testid="cover-unavailable-broken.html"]')).not.toBeNull();
});

test('a replacement cover is retried rather than retaining a previous failure', () => {
  draw({ id: 'changed.html', title: 'Changed', cover: '/covers/old.png' });
  error();
  draw({ id: 'changed.html', title: 'Changed', cover: '/covers/new.png' });
  expect(container.querySelector('img').getAttribute('src')).toBe('/covers/new.png');
  expect(container.querySelector('.fallback-cover')).toBeNull();
});