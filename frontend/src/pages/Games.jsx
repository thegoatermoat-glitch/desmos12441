import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Search, Star, ArrowUpRight, X } from 'lucide-react';
import { CompanionNav } from '../components/Header';
import { GameArtwork } from '../components/games/GameArtwork';
import { GamePlayer } from '../components/games/GamePlayer';
import { api, readStorage, writeStorage } from '../lib/api';

const featured = ['2048.html', 'google-dino.html', 'wordle-unlimited.html', 'slope.html', 'flappy-bird.html', 'chess.html'];
export default function Games() {
  const [games, setGames] = useState([]), [error, setError] = useState(''), [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(''), [category, setCategory] = useState('All');
  const [favorites, setFavorites] = useState(() => readStorage('game-favorites', []));
  const { gameId } = useParams();
  const load = () => { setLoading(true); setError(''); api('/games').then(setGames).catch(e => setError(e.message)).finally(() => setLoading(false)); };
  useEffect(load, []);
  useEffect(() => writeStorage('game-favorites', favorites), [favorites]);
  const sorted = useMemo(() => [...games].sort((a, b) => {
    const ai = featured.indexOf(a.id), bi = featured.indexOf(b.id);
    return (ai < 0 ? 100 : ai) - (bi < 0 ? 100 : bi) || a.title.localeCompare(b.title);
  }), [games]);
  const filtered = sorted.filter(g => g.title.toLowerCase().includes(query.toLowerCase()) && (category === 'All' || category === g.category || (category === 'Favorites' && favorites.includes(g.id))));
  const game = games.find(g => g.id === gameId);
  return <main className="companion-page" data-testid="games-page"><CompanionNav />
    {gameId && game ? <GamePlayer game={game} /> : <div className="library-content">
      <div className="page-heading"><h1 data-testid="games-heading">Library</h1><span className="library-total" data-testid="games-count">{loading ? 'Loading…' : `${games.length} titles`}</span></div>
      {gameId && !loading && !game && <div className="error-banner" data-testid="game-not-found">This title isn't in the library.</div>}
      <div className="library-controls"><div className="search-field"><Search size={18} /><input aria-label="Search library" placeholder="Search library" data-testid="games-search" value={query} onChange={e => setQuery(e.target.value)} />{query && <button className="icon-button" title="Clear search" data-testid="games-clear-search" onClick={() => setQuery('')}><X size={16} /></button>}</div><span className="results-count" data-testid="games-result-count">{filtered.length} results</span></div>
      <div className="category-tabs" data-testid="game-categories">{['All', 'Arcade', 'Puzzle', 'Action', 'Racing', 'Sports', 'Favorites'].map(c => <button key={c} data-testid={`game-category-${c.toLowerCase().replace(' ', '-')}`} className={category === c ? 'active' : ''} onClick={() => setCategory(c)}>{c === 'Favorites' && <Star size={14} />}{c}</button>)}</div>
      {error ? <div className="empty-state" data-testid="games-error"><p>{error}</p><button className="primary-button" data-testid="games-retry" onClick={load}>Try again</button></div> : loading ? <div className="game-grid" data-testid="games-loading">{Array.from({ length: 12 }, (_, i) => <div className="game-skeleton" key={i} />)}</div> : !filtered.length ? <div className="empty-state" data-testid="games-empty"><h2>Nothing here yet</h2><p>{category === 'Favorites' ? 'Your starred titles will appear here.' : 'Try another search.'}</p><button className="secondary-button" data-testid="games-reset-filter" onClick={() => { setQuery(''); setCategory('All'); }}>Show everything</button></div> : <div className="game-grid" data-testid="games-grid">{filtered.map(g => <article className="game-card" data-testid={`game-card-${g.id}`} key={g.id}>
        <Link to={`/library/${encodeURIComponent(g.id)}`} className="game-launch" data-testid={`play-${g.id}`}><GameArtwork game={g} /><div className="game-info"><span className="game-category-label">{g.category}</span><h2>{g.title.replace(/\bgame(s)?\b/gi, 'Classic')}</h2><span className="game-play-label">Open <ArrowUpRight size={15} /></span></div></Link>
        <button className={`favorite-button ${favorites.includes(g.id) ? 'is-favorite' : ''}`} title={favorites.includes(g.id) ? 'Remove favorite' : 'Add favorite'} aria-pressed={favorites.includes(g.id)} data-testid={`favorite-${g.id}`} onClick={() => setFavorites(f => f.includes(g.id) ? f.filter(id => id !== g.id) : [...f, g.id])}><Star size={16} fill={favorites.includes(g.id) ? 'currentColor' : 'none'} /></button>
      </article>)}</div>}
      <footer className="library-footer" data-testid="game-source-credit">Collection by CoolDude2349 · Covers from GN-Math. All titles belong to their respective creators.</footer>
    </div>}
  </main>;
}