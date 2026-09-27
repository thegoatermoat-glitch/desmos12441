"""Publisher-verified uncensored/unrestricted models intersected with live pricing."""
import asyncio
import os
import time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, StrictBool, computed_field
from publisher_models import catalogue_evidence, publisher_evidence


class ModelOption(BaseModel):
    id: str
    name: str
    context_length: int
    is_moderated: StrictBool | None = None
    prompt_price: str = '0'
    completion_price: str = '0'
    request_price: str = '0'
    max_completion_tokens: int | None = None
    supports_reasoning: bool = False
    publisher_verified: bool = False
    publisher_label: str | None = None
    publisher_model_name: str | None = None
    publisher_url: str | None = None
    publisher_quote: str | None = None
    publisher_reviewed_on: str | None = None

    @computed_field
    @property
    def is_free(self) -> bool:
        return all(is_zero(value) for value in (self.prompt_price, self.completion_price, self.request_price))


FreeModel = ModelOption  # Compatibility for earlier test fixtures, not a free-only policy.
_models: list[ModelOption] = []
_expires = 0.0
_lock = asyncio.Lock()


def nonnegative_price(value) -> Decimal | None:
    try:
        price = Decimal(str(value))
        return price if price.is_finite() and price >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def is_zero(value) -> bool:
    return nonnegative_price(value) == 0


def free_model_ids_only(model_id: str) -> bool:
    return isinstance(model_id, str) and (model_id == 'openrouter/free' or model_id.endswith(':free'))


def eligible_model(model: ModelOption) -> bool:
    return (publisher_evidence(model.id) is not None and model.publisher_verified is True
            and model.is_moderated is False and not model.id.startswith('openrouter/')
            and all(nonnegative_price(p) is not None for p in (model.prompt_price, model.completion_price))
            and is_zero(model.request_price) and model.context_length > 0)


def parse_catalogue(items: list) -> list[ModelOption]:
    result, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            continue
        model_id, pricing = item.get('id'), item.get('pricing')
        architecture, provider = item.get('architecture'), item.get('top_provider')
        if not isinstance(model_id, str) or not isinstance(pricing, dict) or not isinstance(architecture, dict) or not isinstance(provider, dict):
            continue
        evidence = catalogue_evidence(item)
        if not evidence:
            continue
        if provider.get('is_moderated') is not False or model_id.startswith('openrouter/') or model_id in seen or 'content-safety' in model_id:
            continue
        if any(nonnegative_price(pricing.get(key)) is None for key in ('prompt', 'completion')):
            continue
        # No request fees, separately priced reasoning, tier overrides or write surcharges.
        # Search, tools, images, audio and plugins are never requested by this text route.
        if any(not is_zero(pricing.get(key, '0')) for key in ('request', 'internal_reasoning', 'input_cache_write')) or pricing.get('overrides'):
            continue
        cache_read = nonnegative_price(pricing.get('input_cache_read', '0'))
        if cache_read is None or cache_read > nonnegative_price(pricing['prompt']):
            continue
        inputs = architecture.get('input_modalities')
        if not isinstance(inputs, list) or 'text' not in inputs or architecture.get('output_modalities') != ['text']:
            continue
        parameters = item.get('supported_parameters') or []
        if not isinstance(parameters, list) or 'max_tokens' not in parameters:
            continue
        context = item.get('context_length')
        if not isinstance(context, int) or isinstance(context, bool) or context <= 0:
            continue
        cap = provider.get('max_completion_tokens')
        cap = cap if isinstance(cap, int) and not isinstance(cap, bool) and cap > 0 else None
        name = item.get('name')
        result.append(ModelOption(id=model_id, name=name if isinstance(name, str) and name else model_id,
            context_length=context, is_moderated=False, max_completion_tokens=cap,
            supports_reasoning='reasoning' in parameters, prompt_price=str(pricing['prompt']),
            completion_price=str(pricing['completion']), request_price='0', publisher_verified=True,
            publisher_label=evidence['label'], publisher_model_name=evidence['model_name'],
            publisher_url=evidence['publisher_url'], publisher_quote=evidence['quote'],
            publisher_reviewed_on=evidence['reviewed_on']))
        seen.add(model_id)
    return sorted(result, key=lambda m: (not m.is_free, Decimal(m.prompt_price) + Decimal(m.completion_price), m.name.lower()))


async def get_models(force_refresh: bool = False) -> list[ModelOption]:
    global _models, _expires
    if not force_refresh and _models and time.monotonic() < _expires:
        return _models
    async with _lock:
        if not force_refresh and _models and time.monotonic() < _expires:
            return _models
        configured = urlsplit(os.environ['OPENROUTER_URL'])
        if not configured.path.endswith('/chat/completions'):
            raise HTTPException(503, 'The model service is not configured correctly.')
        endpoint = urlunsplit((configured.scheme, configured.netloc,
            configured.path.removesuffix('/chat/completions') + '/models', '', ''))
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
                rows = response.json()['data']
                if not isinstance(rows, list):
                    raise ValueError('Invalid catalogue')
                models = parse_catalogue(rows)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(503, 'The eligible model list is unavailable. Please try again.')
        if not models:
            raise HTTPException(503, 'No publisher-verified uncensored or unrestricted model is currently available. Ordinary-model fallback is disabled.')
        _models, _expires = models, time.monotonic() + 180
        return models


async def get_free_models() -> list[ModelOption]:
    return [model for model in await get_models() if model.is_free]


def default_model(models: list[ModelOption]) -> str:
    free = [model for model in models if model.is_free]
    preferred = os.environ.get('OPENROUTER_MODEL')
    if free:
        return preferred if any(m.id == preferred for m in free) else free[0].id
    return min(models, key=lambda m: Decimal(m.prompt_price) + Decimal(m.completion_price)).id