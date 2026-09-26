import { useState } from 'react';
import { BookMarked } from 'lucide-react';
import { CompanionNav } from '../components/Header';
import { BrowserTabs } from '../components/browser/BrowserTabs';
import { BrowserTab } from '../components/browser/BrowserTab';
import { BookmarkManager } from '../components/browser/BookmarkManager';
import { useBrowserWorkspace } from '../hooks/useBrowserWorkspace';
import '../browser.css';

export default function Browser() {
  const web = useBrowserWorkspace();
  const [bookmarksOpen, setBookmarksOpen] = useState(false), [draft, setDraft] = useState(null), [request, setRequest] = useState(null);
  const editBookmark = value => { setDraft(value); setBookmarksOpen(true); };
  const openBookmark = url => setRequest({ id: crypto.randomUUID(), tabId: web.activeId, url });
  return <main className="companion-page browser-page" data-testid="browser-page"><CompanionNav />
    <div className="browser-workspace">
      <div className="browser-topline"><span data-testid="browser-title">Web</span>
        <button className="browser-bookmarks-button" title="Bookmarks" data-testid="browser-bookmarks" onClick={() => editBookmark(null)}><BookMarked size={16} />Bookmarks<span data-testid="browser-bookmark-count">{web.bookmarks.length}</span></button>
      </div>
      {web.storageError && <div className="error-banner" role="alert" data-testid="browser-storage-error">{web.storageError}</div>}
      {web.actionError && <div className="error-banner" role="alert" data-testid="browser-action-error">{web.actionError}</div>}
      <BrowserTabs {...web} />
      {web.tabs.map(tab => <section key={tab.id} id={`web-panel-${tab.id}`} role="tabpanel" aria-labelledby={`web-tab-${tab.id}`} hidden={tab.id !== web.activeId} data-testid={`browser-panel-${tab.id}`}>
        {web.mountedIds.has(tab.id) && <BrowserTab tab={tab} selected={tab.id === web.activeId} onUpdate={web.updateTab} bookmarks={web.bookmarks} editBookmark={editBookmark} request={request} />}
      </section>)}
      {bookmarksOpen && <BookmarkManager bookmarks={web.bookmarks} initialDraft={draft} close={() => setBookmarksOpen(false)} save={web.saveBookmark} remove={web.removeBookmark} open={openBookmark} openNew={web.addTab} />}
    </div>
  </main>;
}