import { useState } from 'react';

export const GAME_COVER_FALLBACK = '/assets/game-cover-fallback-logo.png';

const CoverImage = ({ game }) => {
  const [failed, setFailed] = useState(false);
  const [fallbackFailed, setFallbackFailed] = useState(false);
  const fallback = !game.cover?.trim() || failed;
  return <div className={`game-art real-cover${fallback ? ' fallback-cover' : ''}`} data-testid={`artwork-${game.id}`}>
    {fallback && fallbackFailed
      ? <span className="cover-unavailable" role="img" aria-label={`Cover unavailable for ${game.title}`} data-testid={`cover-unavailable-${game.id}`}>Cover unavailable</span>
      : <img key={fallback ? GAME_COVER_FALLBACK : game.cover} src={fallback ? GAME_COVER_FALLBACK : game.cover}
        alt={fallback ? `Default artwork for ${game.title}` : `${game.title} cover`}
        data-testid={`cover-${game.id}`} loading="lazy" decoding="async"
        onError={() => fallback ? setFallbackFailed(true) : setFailed(true)} />}
  </div>;
};

export const GameArtwork = ({ game }) => <CoverImage key={`${game.id}:${game.cover || ''}`} game={game} />;