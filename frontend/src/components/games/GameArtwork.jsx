import { Gamepad2, Flag, Puzzle, Crosshair, Trophy } from 'lucide-react';
import { useState } from 'react';

export const GameArtwork = ({ game }) => {
  const [failed, setFailed] = useState(false);
  if (game.cover && !failed) return <div className="game-art real-cover"><img src={game.cover} alt={`${game.title} cover`} data-testid={`cover-${game.id}`} loading="lazy" decoding="async" onError={() => setFailed(true)} /></div>;
  const is2048 = game.id === '2048.html';
  const Icon = { Puzzle, Racing: Flag, Action: Crosshair, Sports: Trophy, Arcade: Gamepad2 }[game.category];
  return <div className={`game-art art-${game.category.toLowerCase()} ${is2048 ? 'art-2048' : ''}`} aria-hidden="true">
    {is2048 ? <div className="mini-2048">{[2, 4, 8, 16, 32, 64, 128, 256, 2048].map(n => <span key={n} className={`tile-${n}`}>{n}</span>)}</div> : <><span className="game-art-grid" /><Icon size={44} strokeWidth={1.4} /><span className="game-initial">{game.title.split(' ').slice(0, 2).map(s => s[0]).join('')}</span></>}
  </div>;
};