"""Stateless OpenRouter requests. Full conversation history stays in the browser."""
import os
from time import monotonic
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from free_models import ModelOption, default_model, get_models
from free_fallback import Attempt, MAX_ATTEMPTS, complete_with_fallback
from chat_budget import settings

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
    is_paid: bool
    estimated_cost_usd: str
    actual_cost_usd: str | None
    budget_usd: str
    next_model: str


class ModelList(BaseModel):
    models: list[ModelOption]
    default_model: str
    free_only: bool = False
    unmoderated_only: bool = True
    paid_fallback: bool = True
    max_paid_attempts: int = 1
    estimated_budget_usd: str
    max_output_tokens: int
    max_attempts: int = MAX_ATTEMPTS


@router.get('/models', response_model=ModelList)
async def models():
    items = await get_models()
    budget, output = settings()
    return ModelList(models=items, default_model=default_model(items), estimated_budget_usd=format(budget, 'f'), max_output_tokens=output)


@router.post('/completions', response_model=ChatReply)
async def complete(body: ChatRequest):
    started = monotonic()
    available = await get_models(force_refresh=True)
    if not any(m.id == body.model for m in available):
        raise HTTPException(400, 'This model is not currently eligible. Refresh the model list and choose an unmoderated-provider model.')
    if not os.environ.get('OPENROUTER_API_KEY'):
        raise HTTPException(503, 'The service key has not been configured.')
    system = {'role': 'system', 'content': (
        'You are a helpful assistant in an independent scientific calculator companion. '
        'Be accurate, direct and concise. Use Markdown and LaTeX for math. '
        'You are not an official Desmos service. You cannot see other pages unless their '
        'contents are included in this conversation.')}
    result = await complete_with_fallback(os.environ['OPENROUTER_URL'], {
        'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY'],
        'HTTP-Referer': os.environ['APP_ORIGIN'], 'X-Title': 'Scientific Calculator Companion',
        'X-Session-ID': str(body.session_id),
    }, [system] + [m.model_dump() for m in body.messages], body.model, available, started)
    next_model = result['used_model'] if not result['is_paid'] else default_model(available)
    return ChatReply(session_id=str(body.session_id), requested_model=body.model, next_model=next_model, **result)