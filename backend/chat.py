"""Stateless OpenRouter requests. Full conversation history stays in the browser."""
import os
from time import monotonic
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from free_models import FreeModel, default_model, free_model_ids_only, get_free_models
from free_fallback import Attempt, MAX_ATTEMPTS, complete_free

router = APIRouter(prefix='/api/chat')


class Message(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=12000)

    @field_validator('content')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Write a message first.')
        return value


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: UUID
    model: str = Field(min_length=1, max_length=200)
    messages: list[Message] = Field(min_length=1, max_length=41)

    @model_validator(mode='after')
    def validate_history(self):
        if self.messages[-1].role != 'user':
            raise ValueError('The last message must be from you.')
        if sum(len(m.content) for m in self.messages) > 48000:
            raise ValueError('This request is too long. Start a new conversation.')
        return self


class ChatReply(BaseModel):
    session_id: str
    requested_model: str
    model: str
    content: str
    used_model: str
    attempts: list[Attempt]
    fallback_used: bool


class ModelList(BaseModel):
    models: list[FreeModel]
    default_model: str
    free_only: bool = True
    max_attempts: int = MAX_ATTEMPTS


@router.get('/models', response_model=ModelList)
async def models():
    items = await get_free_models()
    return ModelList(models=items, default_model=default_model(items))


@router.post('/completions', response_model=ChatReply)
async def complete(body: ChatRequest):
    started = monotonic()
    if not free_model_ids_only(body.model):
        raise HTTPException(400, 'Only free models are allowed. Paid fallback is disabled.')
    available = await get_free_models()
    if not any(m.id == body.model for m in available):
        raise HTTPException(400, 'This model is not currently listed as free. Choose another model.')
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise HTTPException(503, 'The service key has not been configured.')
    system = {'role': 'system', 'content': (
        'You are a helpful assistant in an independent scientific calculator companion. '
        'Be accurate, direct and concise. Use Markdown and LaTeX for math. '
        'You are not an official Desmos service. You cannot see other pages unless their '
        'contents are included in this conversation.')}
    result = await complete_free(os.environ['OPENROUTER_URL'], {
        'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'],
        'HTTP-Referer': os.environ['APP_ORIGIN'], 'X-Title': 'Scientific Calculator Companion',
        'X-Session-ID': str(body.session_id),
    }, [system] + [m.model_dump() for m in body.messages], body.model, available, started)
    return ChatReply(session_id=str(body.session_id), requested_model=body.model, **result)