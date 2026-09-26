import { useEffect, useRef } from 'react';
import { Globe2, ArrowRight, RotateCcw, ArrowLeft, Loader2, ExternalLink, Star } from 'lucide-react';
import { useProxyBrowser } from '../../hooks/useProxyBrowser';
import { normalizeAddress } from '../../lib/proxy';
import { pageTitle } from '../../lib/browserWorkspace';

export const BrowserTab = ({ tab, selected, onUpdate, bookmarks, editBookmark, request }) => {
  const host = useRef(null), lastRequest = useRef(null);
  const testId = name => selected ? name : `${name}-${tab.id}`;
  const browser = useProxyBrowser(host, { initial: tab, onChange: patch => onUpdate(tab.id, patch), frameId: testId('browser-iframe') });
  const browserRef = useRef(browser); browserRef.current = browser;
  const { status, error, active, address, setAddress, attempts, navigate, frame, retry, mode, shortcuts, canBack, canForward } = browser;
  const busy = ['connecting', 'switching', 'loading'].includes(status);
  useEffect(() => {
    if (request?.tabId === tab.id && request.id !== lastRequest.current && !busy) {
      lastRequest.current = request.id; browserRef.current.navigate(request.url);
    }
  }, [request, tab.id, busy]);
  let externalUrl = '';
  try { externalUrl = normalizeAddress(address); } catch { /* Invalid input must not produce a link. */ }
  const bookmark = bookmarks.find(item => item.url === externalUrl);
  const labels = { idle: 'Not connected', connecting: 'Connecting…', switching: `Trying connection ${active + 1}…`, loading: 'Loading…', connected: `Connected · ${active + 1}`, unavailable: 'Not connected' };
  return <>
    <form className="browser-address-row" onSubmit={event => { event.preventDefault(); navigate(address); }}>
      <button type="button" className="icon-button" title="Back" aria-label="Back" data-testid={testId('browser-back')} disabled={busy || !canBack} onClick={() => frame.current?.back()}><ArrowLeft size={18} /></button>
      <button type="button" className="icon-button" title="Forward" aria-label="Forward" data-testid={testId('browser-forward')} disabled={busy || !canForward} onClick={() => frame.current?.forward()}><ArrowRight size={18} /></button>
      <button type="button" className="icon-button" title="Reload" aria-label="Reload" data-testid={testId('browser-reload')} disabled={busy || !address} onClick={retry}><RotateCcw size={17} /></button>
      <div className="address-input"><Globe2 size={16} /><input aria-label="Website address" autoComplete="url" spellCheck="false" data-testid={testId('browser-address')} placeholder="Website address" value={address} onChange={event => setAddress(event.target.value)} /></div>
      <button type="button" className={`icon-button bookmark-star ${bookmark ? 'is-bookmarked' : ''}`} title={bookmark ? 'Edit bookmark' : 'Bookmark address'} aria-label={bookmark ? 'Edit bookmark' : 'Bookmark address'} aria-pressed={!!bookmark}
        data-testid={testId('browser-bookmark-page')} disabled={!externalUrl} onClick={() => editBookmark(bookmark || { title: pageTitle(externalUrl), url: externalUrl })}><Star size={17} fill={bookmark ? 'currentColor' : 'none'} /></button>
      <button className="primary-button browser-go" disabled={busy || !address.trim()} data-testid={testId('browser-go')} aria-label="Open website">{busy ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />}</button>
    </form>
    <div className="browser-page-status"><span className={`connection-status status-${status}`} data-testid={testId('proxy-status')}><i />{labels[status]}</span></div>
    <div className="browser-viewport"><div ref={host} className={`proxy-frame-host ${status !== 'connected' && status !== 'loading' ? 'is-hidden' : ''}`} data-testid={testId('proxy-frame-host')} />
      {status !== 'connected' && status !== 'loading' && <div className="browser-start" data-testid={testId('browser-start')}>
        <h1 data-testid={testId('browser-heading')}>{status === 'unavailable' ? 'Couldn’t connect' : busy ? 'Connecting…' : 'New tab'}</h1>
        <p data-testid={testId('browser-description')}>{status === 'unavailable' ? 'Try again or open the website in a new tab.' : busy ? 'Checking the connection.' : 'Enter an address above.'}</p>
        {status === 'idle' && <div className="browser-shortcuts">{shortcuts.map(({ id, name, url }) => <button key={id} className="secondary-button" data-testid={testId(`browser-shortcut-${id}`)} onClick={() => navigate(url)}>{name}</button>)}</div>}
        {status === 'unavailable' && <button className="secondary-button" data-testid={testId('proxy-retry')} onClick={retry}><RotateCcw size={16} />Try again</button>}
      </div>}
      {status === 'loading' && <div className="browser-loading" data-testid={testId('website-loading')}><Loader2 className="spin" size={20} />Loading…</div>}
    </div>
    {!!attempts.length && <div className="connection-attempts connection-history" data-testid={testId('proxy-attempts')}>{attempts.map(attempt => <div key={attempt.index} data-testid={testId(`proxy-server-${attempt.index + 1}`)}><span>Connection {attempt.index + 1}</span><span className={attempt.state === 'Unavailable' ? 'attempt-failed' : ''}>{attempt.state}</span></div>)}</div>}
    {error && <div className="error-banner" role="alert" data-testid={testId('browser-error')}>{error}</div>}
    <div className="browser-footer"><span data-testid={testId('browser-limitations')}>{mode === 'reader' ? 'Reader view · Interactive browsing is not configured.' : 'Full-page browsing · Some websites may restrict access.'}</span>
      {externalUrl && <a className="browser-external-link" href={externalUrl} target="_blank" rel="noopener noreferrer" title="Open website in a new browser tab" data-testid={testId('browser-open-external')}><ExternalLink size={14} />Open in new tab</a>}
    </div>
  </>;
};