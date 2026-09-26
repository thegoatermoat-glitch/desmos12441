from fastapi import FastAPI, APIRouter, HTTPException
import asyncio
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
from database import client, db
from chat import router as chat_router
from games import router as games_router
from frontend_host import mount_frontend
from urllib.parse import urlparse

# Create the main app without a prefix
app = FastAPI()


@app.middleware('http')
async def content_origin_boundary(request, call_next):
    content_host = urlparse(os.environ['CONTENT_ORIGIN']).netloc.lower()
    if content_host and request.url.netloc.lower() == content_host:
        path = request.url.path
        if path.startswith('/api/') and path != '/api/config' and not path.startswith('/api/games/'):
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail': 'Not available on the content hostname.'}, status_code=403)
    return await call_next(request)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Scientific Calculator Companion", "status": "ok"}

@api_router.get('/config')
async def public_config():
    return {'wisp_endpoints': os.environ['WISP_ENDPOINTS'].split(','),
            'content_origin': os.environ['CONTENT_ORIGIN'],
            'game_source': os.environ['GAME_SOURCE_URL'],
            'ai_model': os.environ['OPENROUTER_MODEL']}

@api_router.get('/health')
async def health():
    try:
        await asyncio.wait_for(db.command('ping'), timeout=4)
    except Exception:
        raise HTTPException(503, 'Database connection unavailable')
    return {'status': 'ok', 'database': 'connected'}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)
app.include_router(chat_router)
app.include_router(games_router)
mount_frontend(app)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=os.environ['CORS_ORIGINS'].split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()