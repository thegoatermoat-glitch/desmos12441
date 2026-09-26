"""Live free text-model allowlist; no credential is exposed with the catalogue."""
import asyncio
import os
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import HTTPException
from pydantic import BaseModel


class FreeModel(BaseModel):
    id: str
    name: str
    context_length: int
    is_moderated: bool | None = None
    prompt_price: str = '0'
    completion_price: str = '0'
    request_price: str = '0'


_models: list[FreeModel] = []
_expires = 0.0
_lock = asyncio.Lock()


def is_zero(value) -> bool:
    try:
        return Decimal(str(value)) == 0
    except (InvalidOperation, ValueError, TypeError):
        return False


def free_model_ids_only(model_id: str) -> bool:
    return isinstance(model_id, str) and (model_id == 'openrouter/free' or model_id.endswith(':free'))


def parse_catalogue(items: list) -> list[FreeModel]:
    result = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        model_id = item.get('id', '')
        pricing = item.get('pricing') or {}
        architecture = item.get('architecture') or {}
        if not isinstance(pricing, dict) or not isinstance(architecture, dict):
            continue
        if not free_model_ids_only(model_id) or 'content-safety' in model_id or model_id in seen:
            continue
        if not all(is_zero(pricing.get(key)) for key in ('prompt', 'completion')):
            continue
        if not is_zero(pricing.get('request', '0')):
            continue
        if 'text' not in architecture.get('input_modalities', []) or architecture.get('output_modalities') != ['text']:
            continue
        seen.add(model_id)
        # OpenRouter omits optional request pricing when there is no declared fee.
        # Every completion separately enforces zero prompt/completion/request caps.
        result.append(FreeModel(id=model_id, name=item.get('name') or model_id,
            context_length=item.get('context_length') or 0,
            is_moderated=(item.get('top_provider') or {}).get('is_moderated'),
            prompt_price=str(pricing['prompt']), completion_price=str(pricing['completion']),
            request_price=str(pricing.get('request', '0'))))
    return sorted(result, key=lambda m: (m.is_moderated is not False, m.id == 'openrouter/free', m.name.lower()))


async def get_free_models() -> list[FreeModel]:
    global _models, _expires
    if _models and time.monotonic() < _expires:
        return _models
    async with _lock:
        if _models and time.monotonic() < _expires:
            return _models
        configured = urlsplit(os.environ['OPENROUTER_URL'])
        if not configured.path.endswith('/chat/completions'):
            raise HTTPException(503, 'The model service is not configured correctly.')
        endpoint = urlunsplit((configured.scheme, configured.netloc,
            configured.path.removesuffix('/chat/completions') + '/models', '', ''))
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                models = parse_catalogue(response.json()['data'])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(503, 'The free-model list is unavailable. Please try again.')
        if not models:
            raise HTTPException(503, 'No free text models are currently listed.')
        _models, _expires = models, time.monotonic() + 180
        return models


def default_model(models: list[FreeModel]) -> str:
    preferred = os.environ.get('OPENROUTER_MODEL')
    return preferred if any(m.id == preferred for m in models) else models[0].id