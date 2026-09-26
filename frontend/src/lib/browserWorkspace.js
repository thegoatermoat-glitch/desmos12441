import { normalizeAddress } from './proxy';

export const WORKSPACE_KEY = 'calculator-web-workspace-v1';
export const MAX_TABS = 20;
export const pageTitle = url => { try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return 'New tab'; } };
export const newWebTab = (url = '') => ({ id: crypto.randomUUID(), url, title: pageTitle(url), history: url ? [url] : [], position: url ? 0 : -1 });
const validUrl = value => { try { return typeof value === 'string' && value.length <= 4096 ? normalizeAddress(value) : ''; } catch { return ''; } };
const validId = value => typeof value === 'string' && /^[a-zA-Z0-9-]{1,80}$/.test(value);

export function readWorkspace() {
  let data;
  try { data = JSON.parse(localStorage.getItem(WORKSPACE_KEY)); } catch { /* Start safely if storage is unavailable or corrupted. */ }
  const seen = new Set();
  const tabs = (Array.isArray(data?.tabs) ? data.tabs : []).slice(0, MAX_TABS).filter(item => {
    if (!item || !validId(item.id) || seen.has(item.id)) return false;
    seen.add(item.id); return true;
  }).map(item => {
    const url = validUrl(item.url);
    if (!url) return { id: item.id, url: '', title: 'New tab', history: [], position: -1 };
    const history = Array.isArray(item.history) ? item.history.slice(-100).map(validUrl).filter(Boolean) : [];
    let position = Number.isInteger(item.position) ? Math.max(-1, Math.min(item.position, history.length - 1)) : history.length - 1;
    if (url && (position < 0 || history[position] !== url)) { history.push(url); position = history.length - 1; }
    return { id: item.id, url, title: typeof item.title === 'string' && item.title.trim() ? item.title.slice(0, 160) : pageTitle(url), history, position };
  });
  if (!tabs.length) tabs.push(newWebTab());
  const urls = new Set(), bookmarkIds = new Set();
  const bookmarks = (Array.isArray(data?.bookmarks) ? data.bookmarks : []).flatMap(item => {
    const url = validUrl(item?.url);
    if (!url || !validId(item.id) || urls.has(url) || bookmarkIds.has(item.id)) return [];
    urls.add(url); bookmarkIds.add(item.id);
    return [{ id: item.id, url, title: typeof item.title === 'string' && item.title.trim() ? item.title.slice(0, 100) : pageTitle(url) }];
  });
  return { version: 1, tabs, bookmarks, activeId: tabs.some(t => t.id === data?.activeId) ? data.activeId : tabs[0].id };
}