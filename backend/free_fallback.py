"""Bounded, observable fallback across live zero-price model IDs only."""
import asyncio
import math
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic

import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from free_models import FreeModel, free_model_ids_only, is_zero

MAX_ATTEMPTS = 5
TOTAL_BUDGET_SECONDS = 55.0
PER_ATTEMPT_SECONDS = 12.0


class Attempt(BaseModel):
    model: str
    status: int
    reason: str


def candidates(requested: str, models: list[FreeModel]) -> list[FreeModel]:
    eligible = list({m.id: m for m in models if free_model_ids_only(m.id) and
                all(is_zero(p) for p in (m.prompt_price, m.completion_price, m.request_price))}.values())
    selected = next((m for m in eligible if m.id == requested), None)
    if selected is None:
        raise HTTPException(400, 'This model is not currently listed as free. Choose another model.')
    pool = sorted((m for m in eligible if m.id != requested), key=lambda m: (
        m.is_moderated is not False, m.id == 'openrouter/free',
        not bool(re.search(r'\b(small|mini|flash|lightning|lfm|xs)\b', m.name, re.I)), m.name.lower()))
    result, families = [selected], {requested.split('/')[0]}
    for model in pool:
        if model.id.split('/')[0] not in families:
            result.append(model); families.add(model.id.split('/')[0])
        if len(result) == MAX_ATTEMPTS:
            return result
    seen = {m.id for m in result}
    result.extend(m for m in pool if m.id not in seen)
    return result[:MAX_ATTEMPTS]


def error_policy(status: int, error: dict) -> tuple[bool, str]:
    metadata = error.get('metadata') or {}
    if not isinstance(metadata, dict):
        metadata = {}
    message = str(error.get('message', '')).lower()
    kind = str(metadata.get('error_type', '')).lower()
    if status in (401, 402):
        return False, 'account_error'
    if status == 403:
        return False, 'policy_error'
    if status == 429:
        global_limit = any(text in message for text in (
            'free-models-per-day', 'free-models-per-min', 'daily limit', 'daily quota', 'account-wide'))
        global_limit |= metadata.get('quota_scope') == 'account'
        return not global_limit, 'account_limit' if global_limit else 'rate_limited'
    if status == 404:
        unavailable = kind == 'provider_unavailable' or 'no endpoints found' in message
        policy = any(text in message for text in ('data policy', 'privacy', 'guardrail', 'moderation'))
        return unavailable and not policy, 'unavailable' if unavailable and not policy else 'request_error'
    if status == 408:
        return True, 'timeout'
    return status in (500, 502, 503, 504), 'unavailable' if status >= 500 else 'request_error'


def retry_delay(value: str | None) -> float:
    if not value:
        return 0
    try:
        seconds = float(value)
        return max(0, seconds) if math.isfinite(seconds) else 0
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(0, (date - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 0


def failed(status: int, message: str, attempts: list[Attempt], delay: float = 0):
    raise HTTPException(status, detail={'message': message,
        'attempts': [a.model_dump() for a in attempts], 'paid_fallback': False},
        headers={'Retry-After': str(math.ceil(delay))} if delay else None)


async def complete_free(url: str, headers: dict, messages: list[dict], requested: str,
                        models: list[FreeModel], started: float):
    attempts: list[Attempt] = []
    selected = candidates(requested, models)
    async with httpx.AsyncClient() as client:
        for candidate in selected:
            remaining = TOTAL_BUDGET_SECONDS - (monotonic() - started)
            if remaining <= 0:
                break
            timeout = min(PER_ATTEMPT_SECONDS, remaining)
            payload = {'model': candidate.id, 'messages': messages, 'stream': False, 'max_tokens': 1200,
                'provider': {'max_price': {'prompt': 0, 'completion': 0, 'request': 0},
                             'allow_fallbacks': False, 'require_parameters': True}}
            delay = 0
            try:
                response = await asyncio.wait_for(client.post(url, headers=headers, json=payload,
                    timeout=httpx.Timeout(timeout, connect=min(5.0, timeout))), timeout=timeout)
                try:
                    data = response.json()
                except ValueError:
                    data = {}
                if not isinstance(data, dict):
                    data = {}
                error = data.get('error') if isinstance(data.get('error'), dict) else {}
                status = response.status_code
                if status == 200 and not error:
                    try:
                        answer = data['choices'][0]['message']['content']
                    except (KeyError, IndexError, TypeError):
                        answer = None
                    if isinstance(answer, str) and answer.strip():
                        attempts.append(Attempt(model=candidate.id, status=200, reason='answered'))
                        reported_model = data.get('model')
                        actual_model = reported_model.strip() if isinstance(reported_model, str) else ''
                        return {'content': answer.strip(), 'model': actual_model or candidate.id,
                                'used_model': candidate.id, 'attempts': attempts,
                                'fallback_used': len(attempts) > 1}
                    attempts.append(Attempt(model=candidate.id, status=502, reason='empty_reply'))
                else:
                    if status == 200:
                        try: status = int(error.get('code', 502))
                        except (ValueError, TypeError): status = 502
                    retry, reason = error_policy(status, error)
                    attempts.append(Attempt(model=candidate.id, status=status, reason=reason))
                    delay = retry_delay(response.headers.get('Retry-After'))
                    if not retry:
                        descriptions = {
                            401: 'The service key was rejected. Update the server configuration.',
                            402: 'The provider rejected this account or key limit. No paid model was used.',
                            403: 'The provider rejected the request under its policies or account settings.',
                            429: 'The account-wide free request limit is reached. Try again later.',
                        }
                        failed(status if status in (400, 401, 402, 403, 404, 422, 429) else 503,
                            descriptions.get(status, 'The provider could not accept this request. Your draft is saved locally.'), attempts, delay)
            except (httpx.TimeoutException, asyncio.TimeoutError):
                attempts.append(Attempt(model=candidate.id, status=504, reason='timeout'))
            except httpx.HTTPError:
                attempts.append(Attempt(model=candidate.id, status=502, reason='network_error'))
            if len(attempts) < len(selected):
                remaining = TOTAL_BUDGET_SECONDS - (monotonic() - started)
                if delay >= remaining and delay > 0:
                    failed(429, 'The free service asks you to wait before retrying. Your draft is saved locally.', attempts, delay)
                await asyncio.sleep(min(max(.15, delay), max(0, remaining)))
    failed(503, f'No response was available after {len(attempts)} free-model attempts. Your draft is saved; no paid model was used.', attempts)