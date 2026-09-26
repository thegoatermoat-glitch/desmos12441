"""Server-side OpenRouter calls. Session IDs are private, unguessable capabilities."""
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from database import db

router = APIRouter(prefix='/api/chat')


class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class Session(BaseModel):
    id: str
    title: str
    messages: list[Message] = Field(default_factory=list)
    updated_at: str


class MessageInput(BaseModel):
    content: str = Field(min_length=1, max_length=6000)


def valid_id(value: str):
    try:
        return str(uuid.UUID(value))
    except ValueError:
        raise HTTPException(404, 'Conversation not found.')


@router.post('/sessions', response_model=Session, status_code=201)
async def create_session():
    session = Session(id=str(uuid.uuid4()), title='New conversation',
                      updated_at=datetime.now(timezone.utc).isoformat())
    await db.chat_sessions.insert_one(session.model_dump())
    return session


@router.get('/sessions/{session_id}', response_model=Session)
async def get_session(session_id: str):
    doc = await db.chat_sessions.find_one({'id': valid_id(session_id)}, {'_id': 0})
    if not doc:
        raise HTTPException(404, 'Conversation not found.')
    return Session(**doc)


@router.delete('/sessions/{session_id}', status_code=204)
async def delete_session(session_id: str):
    await db.chat_sessions.delete_one({'id': valid_id(session_id)})


@router.post('/sessions/{session_id}/messages', response_model=Session)
async def send_message(session_id: str, body: MessageInput):
    content = body.content.strip()
    if not content:
        raise HTTPException(422, 'Write a message first.')
    session_id = valid_id(session_id)
    now = datetime.now(timezone.utc)
    doc = await db.chat_sessions.find_one_and_update(
        {'id': session_id, '$or': [{'busy_until': {'$exists': False}},
                                   {'busy_until': {'$lte': now.isoformat()}}]},
        {'$set': {'busy_until': (now + timedelta(seconds=95)).isoformat()}},
        projection={'_id': 0}, return_document=ReturnDocument.BEFORE)
    if not doc:
        existing = await db.chat_sessions.find_one({'id': session_id}, {'_id': 0, 'id': 1})
        raise HTTPException(409 if existing else 404,
                            'A response is already on its way.' if existing else 'Conversation not found.')
    try:
        history = doc.get('messages', [])[-38:]
        pending = history + [{'role': 'user', 'content': content}]
        prompt = [{'role': 'system', 'content': (
            'You are a helpful AI assistant in an independent scientific calculator companion. '
            'Be clear, accurate, concise and friendly. Use Markdown and LaTeX for mathematics. '
            'You are not an official Desmos service. Never claim you can see the calculator '
            'or browser unless the user provides its contents.')}]
        async with httpx.AsyncClient(timeout=httpx.Timeout(80, connect=15)) as http:
            response = await http.post(os.environ['OPENROUTER_URL'],
                headers={'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'],
                         'HTTP-Referer': os.environ['APP_ORIGIN'],
                         'X-Title': 'Scientific Calculator Companion'},
                json={'model': os.environ['OPENROUTER_MODEL'],
                      'models': [os.environ['OPENROUTER_MODEL'], os.environ['OPENROUTER_FALLBACK_MODEL']],
                      'messages': prompt + pending,
                      'max_tokens': 1200, 'temperature': 0.4})
        if response.status_code != 200:
            messages = {401: 'The service key was rejected. Update the server configuration.',
                        402: 'The service account has insufficient credits.',
                        429: 'The service is busy or its request limit is reached. Please try again shortly.'}
            raise HTTPException(503, messages.get(response.status_code,
                                'The service is unavailable. Please try again.'))
        answer = response.json()['choices'][0]['message']['content']
        if not isinstance(answer, str) or not answer.strip():
            raise HTTPException(502, 'No response was returned. Please retry.')
        session = Session(id=session_id, title=content[:64] if not history else doc['title'],
                          messages=pending + [{'role': 'assistant', 'content': answer}],
                          updated_at=datetime.now(timezone.utc).isoformat())
        await db.chat_sessions.update_one({'id': session_id}, {'$set': session.model_dump()})
        return session
    except httpx.TimeoutException:
        raise HTTPException(504, 'The response timed out. Your message was not saved; please retry.')
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        raise HTTPException(502, 'Could not get a response. Please try again.')
    finally:
        await db.chat_sessions.update_one({'id': session_id}, {'$unset': {'busy_until': ''}})