"""Fetch only exact GN-Math matches. No fuzzy sequel/variant substitution."""
import asyncio
import json
import os
import re
import unicodedata
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / 'backend/.env')


def normalize(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', value.lower())


async def main():
    source = json.loads((ROOT / 'backend/data/games-source.json').read_text())
    output = ROOT / 'frontend/public/covers'
    output.mkdir(exist_ok=True)
    mapping, failures = {}, []
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.get(os.environ['GN_ZONES_URL'])
        response.raise_for_status()
        by_name = {}
        for zone in response.json():
            by_name.setdefault(normalize(zone.get('name', '')), []).append(zone)
        slots = asyncio.Semaphore(8)

        async def match(item):
            title = Path(item['name']).stem
            choices = by_name.get(normalize(title), [])
            if len(choices) != 1:
                return
            zone = choices[0]
            cover = zone.get('cover', '')
            if not re.fullmatch(r'\{COVER_URL\}/[a-zA-Z0-9_-]+\.png', cover):
                return
            filename = cover.split('/')[-1]
            url = os.environ['GN_COVER_BASE'].rstrip('/') + '/' + filename
            try:
                async with slots:
                    image = await client.get(url)
                image.raise_for_status()
                if not image.content.startswith(b'\x89PNG\r\n\x1a\n') or len(image.content) > 5_000_000:
                    return
                (output / filename).write_bytes(image.content)
                mapping[item['name']] = {'cover': '/covers/' + filename,
                    'source_title': zone['name'], 'source_url': url}
            except httpx.HTTPError:
                failures.append(item['name'])

        await asyncio.gather(*(match(item) for item in source))
    (ROOT / 'backend/data/game-covers.json').write_text(json.dumps(mapping, indent=2, sort_keys=True))
    print(f'GN-Math: {len(mapping)} exact matched covers saved; {len(failures)} download failures; {len(source)-len(mapping)} use fallback.')


if __name__ == '__main__':
    asyncio.run(main())