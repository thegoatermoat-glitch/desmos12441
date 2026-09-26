import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Maximize2, RotateCcw, Loader2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { API, api } from '../../lib/api';

export const GamePlayer = ({ game }) => {
  const [html, setHtml] = useState(''), [error, setError] = useState(''), [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [source, setSource] = useState('');
  const frame = useRef(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(''); setHtml(''); setSource('');
    api('/config', { signal: controller.signal }).then(async config => {
      if (config.content_origin && new URL(config.content_origin).origin !== window.location.origin) {
        setSource(`${config.content_origin}/api/games/${encodeURIComponent(game.id)}/content`);
        setLoading(false); return;
      }
      const r = await fetch(`${API}/games/${encodeURIComponent(game.id)}/content`, { signal: controller.signal });
      if (!r.ok) { const data = await r.json(); throw new Error(data.detail); }
      setHtml(await r.text()); setLoading(false);
    })
      .catch(e => { if (e.name !== 'AbortError') { setError(e.message); setLoading(false); } });
    return () => controller.abort();
  }, [game.id, revision]);
  const fullscreen = async () => {
    try { await frame.current?.requestFullscreen(); } catch { toast.error('Fullscreen is unavailable in this browser.'); }
  };
  return <div className="game-player" data-testid="game-player">
    <div className="player-toolbar"><Link to="/library" className="text-link" data-testid="back-to-games"><ArrowLeft size={16} />Library</Link><h1 data-testid="game-player-title">{game.title.replace(/\bgame(s)?\b/gi, 'Classic')}</h1><div className="player-actions">
      <button className="icon-button" title="Restart" data-testid="restart-game" onClick={() => setRevision(n => n + 1)}><RotateCcw size={18} /></button>
      <button className="icon-button" title="Fullscreen" data-testid="fullscreen-game" disabled={loading || !!error} onClick={fullscreen}><Maximize2 size={18} /></button>
    </div></div>
    <div className="game-stage">
      {loading ? <div className="stage-message" data-testid="game-loading"><Loader2 className="spin" size={28} /><h2>Loading…</h2><p>{Math.max(1, Math.round(game.size / 1024 / 1024))} MB</p></div>
        : error ? <div className="stage-message" data-testid="game-error"><AlertCircle size={30} /><h2>Couldn't open this title</h2><p>{error.replace(/\bgame(s)?\b/gi, 'title')}</p><button className="primary-button" data-testid="game-retry" onClick={() => setRevision(n => n + 1)}>Try again</button></div>
        : <iframe ref={frame} key={`${game.id}-${revision}`} title={game.title} data-testid="game-iframe" src={source || undefined} srcDoc={source ? undefined : html} sandbox={`allow-scripts allow-forms allow-pointer-lock allow-modals${source ? ' allow-same-origin' : ''}`} allow="fullscreen; gamepad; autoplay" referrerPolicy="no-referrer" allowFullScreen />}
    </div>
    <p className="player-caption" data-testid="game-compatibility-note">Some titles need an internet connection. Progress may reset when you leave.</p>
  </div>;
};