"""Only known files from the requested repository can be fetched or served."""
import asyncio
import json
import os
import uuid
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

router = APIRouter(prefix='/api/games')
SOURCE = json.loads((Path(__file__).parent / 'data/games-source.json').read_text())
COVERS = json.loads((Path(__file__).parent / 'data/game-covers.json').read_text())
FILES = {item['name']: item for item in SOURCE
         if item.get('type') == 'file' and item['name'].lower().endswith(('.html', '.htm'))}
download_slots = asyncio.Semaphore(3)
file_locks = {name: asyncio.Lock() for name in FILES}


class Game(BaseModel):
    id: str
    title: str
    category: str
    size: int
    cover: str | None = None


def category(name):
    if any(x in name for x in ('2048', 'wordle', 'chess', 'quiz', 'puzzle', 'cat', 'bloxorz', 'rope')):
        return 'Puzzle'
    if any(x in name for x in ('soccer', 'basket', 'tennis', 'golf', 'ball', 'boxing')):
        return 'Sports'
    if any(x in name for x in ('car', 'race', 'racing', 'bike', 'roads', 'motor', 'drift')):
        return 'Racing'
    if any(x in name for x in ('war', 'shooter', 'tanks', 'zombie', 'battle', 'fighter')):
        return 'Action'
    return 'Arcade'


@router.get('', response_model=list[Game])
async def list_games():
    return [Game(id=name, title=Path(name).stem.replace('-', ' ').replace('_', ' ').title(),
                 category=category(name.lower()), size=item['size'],
                 cover=COVERS.get(name, {}).get('cover')) for name, item in FILES.items()]


@router.get('/{filename}/content', response_class=HTMLResponse)
async def game_content(filename: str, request: Request):
    if filename not in FILES:
        raise HTTPException(404, 'Game not found in this library.')
    if FILES[filename]['size'] > int(os.environ['GAME_MAX_BYTES']):
        raise HTTPException(413, 'This game exceeds the current download limit.')
    cache = Path(os.environ['GAME_CACHE_DIR'])
    cache.mkdir(parents=True, exist_ok=True)
    file_path = cache / filename
    async with file_locks[filename]:
        if not file_path.exists():
            async with download_slots:
                temporary = cache / (uuid.uuid4().hex + '.part')
                try:
                    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as http:
                        async with http.stream('GET', os.environ['GAME_RAW_BASE'] + quote(filename, safe='')) as r:
                            r.raise_for_status()
                            size = 0
                            with temporary.open('wb') as output:
                                async for chunk in r.aiter_bytes(chunk_size=65536):
                                    size += len(chunk)
                                    if size > int(os.environ['GAME_MAX_BYTES']):
                                        raise HTTPException(413, 'This title is too large to load.')
                                    output.write(chunk)
                    temporary.replace(file_path)
                except httpx.HTTPError:
                    raise HTTPException(502, 'The source is unavailable. Please try again.')
                finally:
                    temporary.unlink(missing_ok=True)
    file_path.touch()
    cached = sorted((p for p in cache.iterdir() if p.name in FILES and p.is_file()), key=lambda p: p.stat().st_mtime)
    total = sum(p.stat().st_size for p in cached)
    for old in cached:
        if total <= int(os.environ['GAME_CACHE_MAX_BYTES']):
            break
        if old != file_path and not file_locks[old.name].locked():
            total -= old.stat().st_size
            old.unlink(missing_ok=True)
    isolated_host = urlparse(os.environ['CONTENT_ORIGIN']).netloc
    isolated = bool(isolated_host) and request.url.netloc.lower() == isolated_host.lower()
    sandbox = 'sandbox allow-scripts allow-forms allow-pointer-lock allow-modals'
    if isolated:
        sandbox += ' allow-same-origin'
    return FileResponse(file_path, media_type='text/html', headers={
        'Content-Security-Policy': sandbox,
        'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'public, max-age=86400'})