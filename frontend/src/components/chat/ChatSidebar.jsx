import { Download, MessageSquare, Plus, Trash2 } from 'lucide-react';

export const ChatSidebar = ({ sessions, current, disabled, fresh, open, remove, exportNotes, legacy, importing, importEarlier }) => <aside className="chat-sidebar" data-testid="chat-sidebar">
  <button className="new-chat-button" data-testid="new-conversation" disabled={disabled} onClick={fresh}><Plus size={17} />New conversation</button>
  <div className="sidebar-label" data-testid="history-scope-label">ON THIS DEVICE</div>
  {!sessions.length && <p className="no-conversations" data-testid="no-conversations">A fresh page.</p>}
  <div className="session-list">{sessions.map(session => <div key={session.id} className={`session-item ${session.id === current?.id ? 'active' : ''}`}>
    <button disabled={disabled} className="session-select" data-testid={`session-${session.id}`} onClick={() => open(session)}><MessageSquare size={15} /><span>{session.title}</span></button>
    <button disabled={disabled} className="delete-session" title="Delete conversation" data-testid={`delete-session-${session.id}`} onClick={() => { if (window.confirm('Delete this conversation from this browser?')) remove(session.id); }}><Trash2 size={14} /></button>
  </div>)}</div>
  {!!legacy.length && <button className="import-earlier" disabled={disabled || importing} data-testid="import-earlier-conversations" onClick={importEarlier}>{importing ? 'Importing…' : `Import ${legacy.length} earlier notes`}</button>}
  <button className="export-notes" title="Download notes backup" data-testid="export-conversations" disabled={!sessions.length || disabled} onClick={exportNotes}><Download size={14} />Export notes</button>
  <div className="sidebar-footer"><span data-testid="chat-storage-notice">Saved in this browser only</span></div>
</aside>;