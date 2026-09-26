import { useCallback, useEffect, useRef, useState } from 'react';
import { api, readStorage, writeStorage } from '../lib/api';
import { deleteConversation, getConversation, listConversations, newConversation, requestMessages, saveConversation } from '../lib/chatHistory';

export const useLocalChat = () => {
  const [sessions, setSessions] = useState([]), [current, setCurrent] = useState(null), [input, setInput] = useState('');
  const [models, setModels] = useState([]), [model, setModel] = useState('');
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true);
  const [error, setError] = useState(''), [storageError, setStorageError] = useState(''), [modelError, setModelError] = useState('');
  const [legacy, setLegacy] = useState(() => readStorage('chat-sessions', []));
  const [importing, setImporting] = useState(false);
  const [lastAttempts, setLastAttempts] = useState([]);
  const mounted = useRef(true), sending = useRef(false);
  const currentRef = useRef(current), inputRef = useRef(input), modelRef = useRef(model);
  currentRef.current = current; inputRef.current = input; modelRef.current = model;
  const refresh = useCallback(async () => {
    const values = await listConversations();
    if (mounted.current) setSessions(values);
    return values;
  }, []);
  const loadModels = useCallback(async () => {
    setModelError('');
    try {
      const result = await api('/chat/models');
      if (!mounted.current) return;
      setModels(result.models);
      setModel(previous => result.models.some(m => m.id === previous) ? previous : result.default_model);
    } catch (failure) { if (mounted.current) setModelError(failure.message); }
  }, []);
  useEffect(() => {
    mounted.current = true;
    refresh().then(values => {
      if (!mounted.current) return;
      const lastId = readStorage('last-local-conversation', null);
      const last = values.find(s => s.id === lastId);
      if (last) { setCurrent(last); setInput(last.draft || ''); if (last.model) setModel(last.model); }
    }).catch(() => setStorageError('Browser storage is unavailable. Enable site storage to save notes.'))
      .finally(() => { if (mounted.current) setLoading(false); });
    loadModels();
    const sync = () => refresh().then(values => {
      if (!mounted.current) return;
      const previous = currentRef.current;
      if (!previous) return;
      const updated = values.find(s => s.id === previous.id);
      if (!updated) { setCurrent(null); setInput(''); return; }
      setCurrent(updated);
      if (inputRef.current === previous.draft) setInput(updated.draft || '');
      if (modelRef.current === previous.model && updated.model) setModel(updated.model);
    }).catch(() => {});
    window.addEventListener('notes-updated', sync);
    return () => { mounted.current = false; window.removeEventListener('notes-updated', sync); };
  }, [refresh, loadModels]);
  const open = session => {
    if (sending.current) return;
    setCurrent(session); setInput(session.draft || ''); setError(''); setLastAttempts([]);
    if (models.some(m => m.id === session.model)) setModel(session.model);
    writeStorage('last-local-conversation', session.id);
  };
  const fresh = () => {
    if (sending.current) return;
    setCurrent(null); setInput(''); setError(''); setLastAttempts([]); writeStorage('last-local-conversation', null);
  };
  const remove = async id => {
    if (sending.current) return;
    try { await deleteConversation(id); await refresh(); if (current?.id === id) fresh(); }
    catch { setError('This conversation could not be removed from browser storage.'); }
  };
  const send = async () => {
    if (sending.current || loading || storageError || !input.trim() || !models.some(m => m.id === model)) return;
    sending.current = true; setBusy(true); setError(''); setLastAttempts([]);
    const content = input.trim(), base = current || newConversation(model);
    const requestId = crypto.randomUUID();
    const draft = { ...base, model, draft: content, pending_id: requestId, title: base.messages.length ? base.title : content.slice(0, 64), updated_at: new Date().toISOString() };
    try {
      await saveConversation(draft);
      if (mounted.current) { setCurrent(draft); await refresh(); writeStorage('last-local-conversation', draft.id); }
      const answer = await api('/chat/completions', { method: 'POST', body: JSON.stringify({
        session_id: draft.id, model, messages: requestMessages(draft, content),
      }) });
      const latest = await getConversation(draft.id);
      if (!latest || latest.pending_id !== requestId) return;
      const completed = { ...draft, model: answer.used_model, pending_id: null, draft: '', updated_at: new Date().toISOString(), messages: [...draft.messages,
        { role: 'user', content }, { role: 'assistant', content: answer.content, model: answer.model,
          requested_model: answer.requested_model, used_model: answer.used_model,
          fallback_used: answer.fallback_used, attempts: answer.attempts }] };
      if (mounted.current) { setCurrent(completed); setInput(''); setModel(answer.used_model); setLastAttempts(answer.attempts); }
      await saveConversation(completed); await refresh();
    } catch (failure) {
      if (mounted.current) {
        setLastAttempts(failure.attempts || []);
        setError(failure.name === 'QuotaExceededError'
          ? 'Browser storage is full. Export your notes and remove an older conversation.' : failure.message);
      }
    } finally { sending.current = false; if (mounted.current) setBusy(false); }
  };
  const importEarlier = async () => {
    setImporting(true); setError('');
    const remaining = [];
    for (const item of legacy) {
      try {
        if (!(await listConversations()).some(s => s.id === item.id)) {
          const session = await api(`/chat/sessions/${encodeURIComponent(item.id)}`);
          await saveConversation({ ...session, model, draft: '' });
        }
      } catch { remaining.push(item); }
    }
    writeStorage('chat-sessions', remaining); setLegacy(remaining); await refresh(); setImporting(false);
    if (remaining.length) setError('Some older notes could not be imported. Their original server records were not changed.');
  };
  return { sessions, current, input, setInput, models, model, setModel, busy, loading, error,
    storageError, modelError, loadModels, open, fresh, remove, send, legacy, importing, importEarlier, lastAttempts };
};