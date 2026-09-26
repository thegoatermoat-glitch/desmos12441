import { useState } from 'react';
import { ArrowUpRight, Bookmark, Pencil, Plus, Search, Trash2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { BookmarkEditor } from './BookmarkEditor';

export const BookmarkManager = ({ bookmarks, initialDraft, close, save, remove, open, openNew }) => {
  const [draft, setDraft] = useState(initialDraft), [search, setSearch] = useState('');
  const filtered = bookmarks.filter(item => `${item.title} ${item.url}`.toLowerCase().includes(search.toLowerCase()));
  const saved = bookmark => { save(bookmark); setDraft(null); };
  return <Dialog open onOpenChange={value => { if (!value) close(); }}>
    <DialogContent className="bookmark-dialog" aria-describedby={undefined} data-testid="bookmark-dialog">
      <DialogHeader><DialogTitle data-testid="bookmark-dialog-title">{draft ? draft.id ? 'Edit bookmark' : 'New bookmark' : 'Bookmarks'}</DialogTitle></DialogHeader>
      {draft ? <BookmarkEditor key={draft.id || 'new'} initial={draft} save={saved} cancel={() => setDraft(null)} remove={id => { remove(id); setDraft(null); }} /> : <>
        <div className="bookmark-tools">
          <label className="bookmark-search"><Search size={15} /><input aria-label="Search bookmarks" data-testid="bookmark-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search bookmarks" /></label>
          <button className="icon-button" title="Add bookmark" aria-label="Add bookmark" data-testid="bookmark-add" onClick={() => setDraft({ title: '', url: '' })}><Plus size={19} /></button>
        </div>
        <div className="bookmark-list" data-testid="bookmark-list">
          {!filtered.length && <p className="bookmark-empty" data-testid="bookmark-empty">{bookmarks.length ? 'No matching bookmarks' : 'No bookmarks yet'}</p>}
          {filtered.map(item => <div className="bookmark-row" key={item.id} data-testid={`bookmark-row-${item.id}`}>
            <button className="bookmark-open" title={item.url} data-testid={`bookmark-open-${item.id}`} onClick={() => { open(item.url); close(); }}>
              <Bookmark size={16} /><span><strong data-testid={`bookmark-title-${item.id}`}>{item.title}</strong><small data-testid={`bookmark-address-${item.id}`}>{item.url}</small></span>
            </button>
            <button className="icon-button" title="Open bookmark in new Web tab" aria-label={`Open ${item.title} in new Web tab`} data-testid={`bookmark-new-tab-${item.id}`} onClick={() => { openNew(item.url); close(); }}><ArrowUpRight size={16} /></button>
            <button className="icon-button" title="Edit bookmark" aria-label={`Edit ${item.title}`} data-testid={`bookmark-edit-${item.id}`} onClick={() => setDraft(item)}><Pencil size={14} /></button>
            <button className="icon-button" title="Remove bookmark" aria-label={`Remove ${item.title}`} data-testid={`bookmark-delete-${item.id}`} onClick={() => remove(item.id)}><Trash2 size={14} /></button>
          </div>)}
        </div>
      </>}
    </DialogContent>
  </Dialog>;
};