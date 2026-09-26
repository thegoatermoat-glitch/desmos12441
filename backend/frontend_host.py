"""Production SPA hosting. Preview continues to use its existing React service."""
import os
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse


def mount_frontend(app):
    if os.environ['SERVE_FRONTEND'].lower() != 'true':
        return
    root = Path(os.environ['FRONTEND_BUILD_DIR']).resolve()
    if not (root / 'index.html').is_file():
        raise RuntimeError('FRONTEND_BUILD_DIR must contain the compiled frontend')

    @app.get('/{path:path}', include_in_schema=False)
    async def frontend(path: str):
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404, 'Endpoint not found')
        if path.startswith('browse/service/'):
            raise HTTPException(503, 'The content service is not controlling this page. Use a separate content hostname.')
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            raise HTTPException(404, 'Not found')
        if target.is_file():
            response = FileResponse(target)
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable' if path.startswith('static/') else 'no-cache'
            if path.endswith('.wasm'):
                response.headers['Content-Type'] = 'application/wasm'
            if path.endswith('.mjs'):
                response.headers['Content-Type'] = 'application/javascript'
            return response
        if Path(path).suffix:
            raise HTTPException(404, 'File not found')
        return FileResponse(root / 'index.html', headers={'Cache-Control': 'no-cache'})