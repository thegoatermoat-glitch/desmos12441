import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Plus, MessageSquare, Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { CompanionNav } from '../components/Header';
import { ChatMessage } from '../components/chat/ChatMessage';
import { api, readStorage, writeStorage } from '../lib/api';

export default function Chat() {
  const [sessions, setSessions] = useState(() => readStorage('chat-sessions', []));
  const [current, setCurrent] = useState(null), [input, setInput] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [loading, setLoading] = useState(false);
  const bottom = useRef(null), textbox = useRef(null);
  useEffect(() => { writeStorage('chat-sessions', sessions); }, [sessions]);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [current, busy]);
  const remember = session => setSessions(prev => [{ id: session.id, title: session.title }, ...prev.filter(s => s.id !== session.id)].slice(0, 30));
  const openSession = async id => {
    setLoading(true); setError('');
    try { const session = await api(`/chat/sessions/${id}`); setCurrent(session); setInput(''); } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  const remove = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try { await api(`/chat/sessions/${id}`, { method: 'DELETE' }); setSessions(prev => prev.filter(s => s.id !== id)); if (current?.id === id) setCurrent(null); } catch (e) { toast.error(e.message); }
  };
  const send = async (event) => {
    event?.preventDefault();
    if (!input.trim() || busy || loading) return;
    const content = input.trim(); setBusy(true); setError('');
    let session = current;
    try {
      if (!session) { session = await api('/chat/sessions', { method: 'POST' }); setCurrent(session); remember(session); }
      const result = await api(`/chat/sessions/${session.id}/messages`, { method: 'POST', body: JSON.stringify({ content }) });
      setCurrent(result); remember(result); setInput('');
    } catch (e) { setError(e.message); } finally { setBusy(false); textbox.current?.focus(); }
  };
  return <main className="companion-page chat-page" data-testid="chat-page"><CompanionNav /><div className="chat-layout">
    <aside className="chat-sidebar" data-testid="chat-sidebar"><button className="new-chat-button" data-testid="new-conversation" disabled={busy || loading} onClick={() => { setCurrent(null); setInput(''); setError(''); textbox.current?.focus(); }}><Plus size={17} />New conversation</button><div className="sidebar-label">YOUR CONVERSATIONS</div>
      {!sessions.length && <p className="no-conversations" data-testid="no-conversations">A fresh page.</p>}
      <div className="session-list">{sessions.map(s => <div key={s.id} className={`session-item ${s.id === current?.id ? 'active' : ''}`}><button disabled={busy || loading} className="session-select" data-testid={`session-${s.id}`} onClick={() => openSession(s.id)}><MessageSquare size={15} /><span>{s.title}</span></button><button disabled={busy || loading} className="delete-session" title="Delete conversation" data-testid={`delete-session-${s.id}`} onClick={e => remove(e, s.id)}><Trash2 size={14} /></button></div>)}</div>
      <div className="sidebar-footer"><span data-testid="chat-provider">Notes</span></div>
    </aside>
    <section className="chat-main"><div className="chat-topline"><span data-testid="conversation-title">{current?.title || 'New conversation'}</span></div>
      <div className="chat-scroll" data-testid="chat-scroll">
        {loading ? <div className="stage-message" data-testid="conversation-loading"><Loader2 className="spin" />Loading conversation…</div> : current?.messages?.length ? <div className="messages">{current.messages.map((m, i) => <ChatMessage message={m} index={i} key={i} />)}</div> : <div className="chat-empty" data-testid="chat-empty"><h1>Notes</h1><p>What would you like to work on?</p></div>}
        {busy && <div className="pending-message" data-testid="chat-thinking"><div className="pending-user">{input}</div><span><i /><i /><i /></span></div>}<div ref={bottom} />
      </div>
      <div className="composer-area">{error && <div className="error-banner" role="alert" data-testid="chat-error">{error}</div>}<form className="chat-composer" onSubmit={send}><textarea ref={textbox} data-testid="chat-input" aria-label="Write a message" value={input} maxLength={6000} disabled={busy || loading} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} placeholder="Write a message…" rows={2} /><div className="composer-bottom"><span /><button type="submit" title="Send message" aria-label="Send message" data-testid="chat-send" disabled={!input.trim() || busy || loading}>{busy ? <Loader2 className="spin" size={18} /> : <ArrowUp size={20} />}</button></div></form><p className="chat-disclaimer" data-testid="chat-disclaimer">Double-check important answers.</p></div>
    </section>
  </div></main>;
}