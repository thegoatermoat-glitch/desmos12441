import { useEffect, useRef } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';
import { CompanionNav } from '../components/Header';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatSidebar } from '../components/chat/ChatSidebar';
import { ModelPicker } from '../components/chat/ModelPicker';
import { ModelAttempts } from '../components/chat/ModelAttempts';
import { downloadConversations } from '../lib/chatHistory';
import { useLocalChat } from '../hooks/useLocalChat';

export default function Chat() {
  const chat = useLocalChat();
  const conversation = chat.current;
  const bottom = useRef(null), textbox = useRef(null);
  const disabled = chat.busy || chat.loading || !!chat.storageError;
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [conversation, chat.busy]);
  const send = async event => { event?.preventDefault(); await chat.send(); textbox.current?.focus(); };
  const backup = () => downloadConversations(chat.current
    ? [chat.current, ...chat.sessions.filter(s => s.id !== chat.current.id)] : chat.sessions);
  return <main className="companion-page chat-page ph-no-capture" data-testid="chat-page"><CompanionNav /><div className="chat-layout">
    <ChatSidebar {...chat} disabled={disabled} exportNotes={backup} />
    <section className="chat-main">
      <div className="chat-topline"><span data-testid="conversation-title">{chat.current?.title || 'New conversation'}</span>
        <ModelPicker models={chat.models} value={chat.model} onChange={chat.setModel} disabled={disabled} error={chat.modelError} retry={chat.loadModels} />
      </div>
      <div className="chat-scroll" data-testid="chat-scroll">
        {chat.loading ? <div className="stage-message" data-testid="conversation-loading"><Loader2 className="spin" />Opening notes…</div>
          : chat.current?.messages?.length ? <div className="messages">{chat.current.messages.map((m, index) => <ChatMessage message={m} index={index} key={index} />)}</div>
          : <div className="chat-empty" data-testid="chat-empty"><h1 data-testid="notes-heading">Notes</h1><p>What would you like to work on?</p></div>}
        {chat.busy && <div className="pending-message" data-testid="chat-thinking"><div className="pending-user">{chat.input}</div><span role="status" aria-label="Waiting for a free response" data-testid="chat-pending-status"><i /><i /><i /></span></div>}<div ref={bottom} />
      </div>
      <div className="composer-area">
        {(chat.error || chat.storageError || chat.modelError) && <div className="error-banner" role="alert" data-testid="chat-error">{chat.storageError || chat.error || chat.modelError}</div>}
        {chat.error && <ModelAttempts attempts={chat.lastAttempts} testId="chat-failed-attempts" />}
        <form className="chat-composer" onSubmit={send}><textarea ref={textbox} data-testid="chat-input" aria-label="Write a message" value={chat.input} maxLength={6000} disabled={disabled}
          onChange={event => chat.setInput(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Write a message…" rows={2} />
          <div className="composer-bottom"><span data-testid="chat-cost-notice">Up to 5 free models · No paid fallback</span>
            <button type="submit" title="Send message" aria-label="Send message" data-testid="chat-send" disabled={!chat.input.trim() || disabled || !chat.models.some(m => m.id === chat.model)}>{chat.busy ? <Loader2 className="spin" size={18} /> : <ArrowUp size={20} />}</button>
          </div>
        </form><p className="chat-disclaimer" data-testid="chat-disclaimer">History stays on this device; requests go to OpenRouter and its providers. Check important answers.</p>
      </div>
    </section>
  </div></main>;
}