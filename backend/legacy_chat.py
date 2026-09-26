"""Optional, explicit READ-ONLY import from an existing database. Never used at startup."""
import os
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from chat import Message

router = APIRouter(prefix='/api/chat/sessions')


class LegacySession(BaseModel):
    id: str
    title: str
    messages: list[Message]
    updated_at: str


@router.get('/{session_id}', response_model=LegacySession)
async def import_previous_session(session_id: str):
    try:
        session_id = str(UUID(session_id))
    except ValueError:
        raise HTTPException(404, 'Conversation not found.')
    uri, name = os.environ.get('MONGO_URL'), os.environ.get('DB_NAME')
    if not uri or not name:
        raise HTTPException(410, 'The original server history is not connected. New notes are saved in this browser.')
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import PyMongoError
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=2500, connectTimeoutMS=1500)
    try:
        doc = await client[name].chat_sessions.find_one({'id': session_id}, {'_id': 0})
        if not doc:
            raise HTTPException(404, 'The earlier conversation was not found.')
        return LegacySession(**doc)
    except PyMongoError:
        raise HTTPException(410, 'The original server history is unavailable. New notes do not need it.')
    finally:
        client.close()


@router.post('')
@router.post('/{session_id}/messages')
@router.delete('/{session_id}')
async def retired_server_storage(session_id: str | None = None):
    raise HTTPException(410, 'Conversations are now managed in the browser. Reload the application.')