import { readWorkspace, WORKSPACE_KEY } from './browserWorkspace';

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, 'crypto', { configurable: true, value: { randomUUID: () => 'fresh-test-tab' } });
});

test('unsafe restored tabs become canonical blank tabs, without stale title or history', () => {
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({
    activeId: 'bad-tab',
    tabs: [
      { id: 'bad-tab', url: 'javascript:alert(1)', title: 'bad', history: ['https://example.com/'], position: 0 },
      { id: 'bad-tab', url: 'https://example.com/', title: 'duplicate' },
    ], bookmarks: [],
  }));
  const restored = readWorkspace();
  expect(restored.tabs).toEqual([{ id: 'bad-tab', url: '', title: 'New tab', history: [], position: -1 }]);
  expect(restored.activeId).toBe('bad-tab');
});

test('valid tab addresses, titles and independent history positions survive restore', () => {
  const tabs = [
    { id: 'tab-a', url: 'https://example.com/', title: 'Example', history: ['https://example.com/', 'https://www.iana.org/'], position: 0 },
    { id: 'tab-b', url: 'https://www.youtube.com/', title: 'YouTube', history: ['https://www.youtube.com/'], position: 0 },
  ];
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({ tabs, activeId: 'tab-b', bookmarks: [] }));
  const restored = readWorkspace();
  expect(restored.tabs).toEqual(tabs);
  expect(restored.activeId).toBe('tab-b');
});

test('restored bookmarks reject unsafe URLs and deduplicate normalized addresses', () => {
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify({ bookmarks: [
    { id: 'safe-a', title: 'Saved', url: 'https://example.com' },
    { id: 'safe-b', title: 'Duplicate', url: 'https://example.com/' },
    { id: 'unsafe', title: 'Unsafe', url: 'javascript:alert(1)' },
    { id: 'local', title: 'Private', url: 'http://127.0.0.1/' },
  ] }));
  expect(readWorkspace().bookmarks).toEqual([{ id: 'safe-a', title: 'Saved', url: 'https://example.com/' }]);
});

test('corrupted storage restores one usable blank tab', () => {
  localStorage.setItem(WORKSPACE_KEY, '{');
  const restored = readWorkspace();
  expect(restored.tabs).toEqual([{ id: 'fresh-test-tab', url: '', title: 'New tab', history: [], position: -1 }]);
  expect(restored.activeId).toBe('fresh-test-tab');
});