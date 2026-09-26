import { useCallback, useEffect, useRef, useState } from 'react';
import { MAX_TABS, newWebTab, readWorkspace, WORKSPACE_KEY } from '../lib/browserWorkspace';
import { normalizeAddress } from '../lib/proxy';

export const useBrowserWorkspace = () => {
  const [workspace, setWorkspace] = useState(readWorkspace);
  const [storageError, setStorageError] = useState('');
  const [actionError, setActionError] = useState('');
  const [mountedIds, setMountedIds] = useState(() => new Set([workspace.activeId]));
  const latest = useRef(workspace); latest.current = workspace;
  useEffect(() => {
    try { localStorage.setItem(WORKSPACE_KEY, JSON.stringify(workspace)); setStorageError(''); }
    catch { setStorageError('Browser storage is unavailable or full. Tabs and bookmarks are kept for this visit only.'); }
  }, [workspace]);
  const activate = useCallback(id => {
    if (!latest.current.tabs.some(tab => tab.id === id)) return;
    setMountedIds(previous => new Set([...previous, id]));
    setWorkspace(previous => ({ ...previous, activeId: id }));
  }, []);
  const addTab = useCallback((value = '') => {
    if (latest.current.tabs.length >= MAX_TABS) { setActionError('Close a tab before opening another. The limit is 20 tabs.'); return; }
    let url = '';
    try { if (value) url = normalizeAddress(value); } catch (error) { setActionError(error.message); return; }
    setActionError('');
    const tab = newWebTab(url);
    setMountedIds(previous => new Set([...previous, tab.id]));
    setWorkspace(previous => ({ ...previous, tabs: [...previous.tabs, tab], activeId: tab.id }));
  }, []);
  const closeTab = useCallback(id => {
    setActionError('');
    const current = latest.current, index = current.tabs.findIndex(tab => tab.id === id);
    if (index < 0) return;
    const tabs = current.tabs.filter(tab => tab.id !== id);
    if (!tabs.length) tabs.push(newWebTab());
    const activeId = id === current.activeId ? tabs[Math.min(index, tabs.length - 1)].id : current.activeId;
    setMountedIds(previous => new Set([...previous].filter(key => key !== id).concat(activeId)));
    setWorkspace(previous => ({ ...previous, tabs, activeId }));
  }, []);
  const updateTab = useCallback((id, patch) => {
    setWorkspace(previous => {
      const tab = previous.tabs.find(item => item.id === id);
      if (!tab || Object.entries(patch).every(([key, value]) => JSON.stringify(tab[key]) === JSON.stringify(value))) return previous;
      return { ...previous, tabs: previous.tabs.map(item => item.id === id ? { ...item, ...patch } : item) };
    });
  }, []);
  const saveBookmark = useCallback(bookmark => {
    const title = bookmark.title.trim(), url = normalizeAddress(bookmark.url);
    if (!title) throw new Error('Enter a bookmark name.');
    if (latest.current.bookmarks.some(item => item.url === url && item.id !== bookmark.id)) throw new Error('This address is already bookmarked.');
    const entry = { id: bookmark.id || crypto.randomUUID(), title: title.slice(0, 100), url };
    setWorkspace(previous => ({ ...previous, bookmarks: bookmark.id
      ? previous.bookmarks.map(item => item.id === bookmark.id ? entry : item) : [...previous.bookmarks, entry] }));
    return entry;
  }, []);
  const removeBookmark = useCallback(id => setWorkspace(previous => ({ ...previous, bookmarks: previous.bookmarks.filter(item => item.id !== id) })), []);
  return { ...workspace, storageError, actionError, mountedIds, activate, addTab, closeTab, updateTab, saveBookmark, removeBookmark };
};