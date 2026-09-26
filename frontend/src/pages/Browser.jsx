import { useRef } from 'react';
import { Globe2, ArrowRight, RotateCcw, ArrowLeft, Loader2 } from 'lucide-react';
import { CompanionNav } from '../components/Header';
import { useProxyBrowser } from '../hooks/useProxyBrowser';

export default function Browser() {
  const host = useRef(null);
  const { status, error, active, address, setAddress, attempts, navigate, frame, retry, mode } = useProxyBrowser(host);
  const busy = ['connecting', 'switching', 'loading'].includes(status);
  const labels = { idle: 'Not connected', connecting: 'Connecting…', switching: 'Trying connection 2…', loading: 'Loading…', connected: `Connected · ${active + 1}`, unavailable: 'Not connected' };
  return <main className="companion-page browser-page" data-testid="browser-page"><CompanionNav />
    <div className="browser-workspace"><div className="browser-topline"><span>Web</span><span className={`connection-status status-${status}`} data-testid="proxy-status"><i />{labels[status]}</span></div>
      <form className="browser-address-row" onSubmit={e => { e.preventDefault(); navigate(address); }}>
        <button type="button" className="icon-button" title="Back" data-testid="browser-back" disabled={status !== 'connected'} onClick={() => frame.current?.back()}><ArrowLeft size={18} /></button>
        <button type="button" className="icon-button" title="Forward" data-testid="browser-forward" disabled={status !== 'connected'} onClick={() => frame.current?.forward()}><ArrowRight size={18} /></button>
        <button type="button" className="icon-button" title="Reload" data-testid="browser-reload" disabled={busy || !address} onClick={retry}><RotateCcw size={17} /></button>
        <div className="address-input"><Globe2 size={16} /><input aria-label="Website address" autoComplete="url" spellCheck="false" data-testid="browser-address" placeholder="Website address" value={address} onChange={e => setAddress(e.target.value)} /></div>
        <button className="primary-button browser-go" disabled={busy || !address.trim()} data-testid="browser-go" aria-label="Open website">{busy ? <Loader2 size={18} className="spin" /> : <ArrowRight size={18} />}</button>
      </form>
      <div className="browser-viewport"><div ref={host} className={`proxy-frame-host ${status !== 'connected' && status !== 'loading' ? 'is-hidden' : ''}`} data-testid="proxy-frame-host" />
        {status !== 'connected' && status !== 'loading' && <div className="browser-start" data-testid="browser-start">
          <h1 data-testid="browser-heading">{status === 'unavailable' ? 'Couldn’t connect' : busy ? 'Connecting…' : 'New page'}</h1>
          <p data-testid="browser-description">{status === 'unavailable' ? 'Please try again in a moment.' : busy ? 'Checking the next connection.' : 'Enter an address above.'}</p>
          {status === 'idle' && <div className="browser-shortcuts">{[['Wikipedia', 'https://www.wikipedia.org'], ['Example', 'https://example.com']].map(([name, url]) => <button key={name} className="secondary-button" data-testid={`browser-shortcut-${name.toLowerCase()}`} onClick={() => navigate(url)}>{name}</button>)}</div>}
          {status === 'unavailable' && <button className="secondary-button" data-testid="proxy-retry" onClick={retry}><RotateCcw size={16} />Try again</button>}
        </div>}
        {status === 'loading' && <div className="browser-loading" data-testid="website-loading"><Loader2 className="spin" size={20} />Loading…</div>}
      </div>
      {!!attempts.length && <div className="connection-attempts connection-history" data-testid="proxy-attempts">{attempts.map(a => <div key={a.index} data-testid={`proxy-server-${a.index + 1}`}><span>Connection {a.index + 1}</span><span className={a.state === 'Unavailable' ? 'attempt-failed' : ''}>{a.state}</span></div>)}</div>}
      {error && <div className="error-banner" role="alert" data-testid="browser-error">{error}</div>}
      <div className="browser-footer"><span data-testid="browser-limitations">{mode === 'reader' ? 'Reader view · Interactive pages need a separate content hostname.' : 'Some websites may not open here.'}</span></div>
    </div>
  </main>;
}