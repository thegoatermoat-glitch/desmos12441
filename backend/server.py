import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / '.env')

from chat import router as chat_router
from legacy_chat import router as legacy_router
from games import router as games_router
from frontend_host import mount_frontend

app = FastAPI()
api_router = APIRouter(prefix='/api')


@app.middleware('http')
async def content_origin_boundary(request, call_next):
    content_host = urlparse(os.environ['CONTENT_ORIGIN']).netloc.lower()
    if content_host and request.url.netloc.lower() == content_host:
        path = request.url.path
        if path.startswith('/api/') and path != '/api/config' and not path.startswith('/api/games/'):
            return JSONResponse({'detail': 'Not available on the content hostname.'}, status_code=403)
    return await call_next(request)


@api_router.get('/')
async def root():
    return {'message': 'Scientific Calculator Companion', 'status': 'ok'}


@api_router.get('/config')
async def public_config():
    return {'wisp_endpoints': os.environ['WISP_ENDPOINTS'].split(','),
            'content_origin': os.environ['CONTENT_ORIGIN'],
            'game_source': os.environ['GAME_SOURCE_URL'],
            'history_storage': 'browser', 'free_models_only': True,
            'legacy_import_available': bool(os.environ.get('MONGO_URL') and os.environ.get('DB_NAME'))}


@api_router.get('/health')
async def health():
    return {'status': 'ok', 'storage': 'browser', 'database_required': False}


@api_router.get('/status')
@api_router.post('/status')
async def retired_status_records():
    raise HTTPException(410, 'Stored status records were retired. Use /api/health.')


app.include_router(api_router)
app.include_router(chat_router)
app.include_router(legacy_router)
app.include_router(games_router)
mount_frontend(app)
app.add_middleware(CORSMiddleware, allow_credentials=False,
    allow_origins=os.environ['CORS_ORIGINS'].split(','), allow_methods=['*'], allow_headers=['*'])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')