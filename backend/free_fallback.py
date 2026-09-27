"""Free-first unmoderated-model routing, then at most one cheapest paid attempt."""
import asyncio
import math
import re
from decimal import Decimal
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import monotonic

import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from free_models import ModelOption, eligible_model
from chat_budget import settings, prompt_bound, output_limit, estimate, provider_limits, reported_cost

MAX_ATTEMPTS = 5
TOTAL_BUDGET_SECONDS = 55.0
PER_ATTEMPT_SECONDS = 12.0


class Attempt(BaseModel):
    model: str
    status: int
    reason: str
    is_paid: bool = False
    estimated_cost_usd: str = '0'
    actual_cost_usd: str | None = None


def candidates(requested: str, models: list[ModelOption], messages: list[dict] | None = None) -> list[ModelOption]:
    budget, configured_output = settings()
    tokens = prompt_bound(messages or [])
    eligible = list({m.id: m for m in models if eligible_model(m)}.values())
    selected = next((m for m in eligible if m.id == requested), None)
    if selected is None:
        raise HTTPException(400, 'Choose a currently listed model with an explicitly unmoderated provider and known pricing.')
    eligible = [m for m in eligible if tokens + output_limit(m, configured_output) <= m.context_length]
    pool = sorted((m for m in eligible if m.is_free and m.id != requested), key=lambda m: (
        not bool(re.search(r'\b(small|mini|flash|lightning|lfm|xs)\b', m.name, re.I)), m.name.lower()))
    result = [selected] if selected.is_free and selected in eligible else []
    families = {m.id.split('/')[0] for m in result}
    for model in pool:
        if model.id.split('/')[0] not in families:
            result.append(model); families.add(model.id.split('/')[0])
    seen = {m.id for m in result}
    result.extend(m for m in pool if m.id not in seen)
    paid = sorted((m for m in eligible if not m.is_free and estimate(m, tokens, configured_output) <= budget),
                  key=lambda m: (estimate(m, tokens, configured_output), m.id))
    return result[:MAX_ATTEMPTS - 1] + paid[:1] if paid else result[:MAX_ATTEMPTS]


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
        if any(text in message for text in ('free-models-per-day', 'free-models-per-min')) or metadata.get('quota_scope') == 'free':
            return True, 'free_limit'
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
    paid_attempted = any(attempt.is_paid for attempt in attempts)
    if paid_attempted:
        message += ' A paid request was attempted and may have incurred a charge; no further paid request was sent.'
    raise HTTPException(status, detail={'message': message,
        'attempts': [a.model_dump() for a in attempts], 'paid_fallback': True, 'paid_attempted': paid_attempted},
        headers={'Retry-After': str(math.ceil(delay))} if delay else None)


async def complete_with_fallback(url: str, headers: dict, messages: list[dict], requested: str,
                                 models: list[ModelOption], started: float):
    attempts: list[Attempt] = []
    selected = candidates(requested, models, messages)
    budget, configured_output = settings()
    tokens, reserved, skip_free = prompt_bound(messages), Decimal('0'), False
    if not selected:
        failed(400, 'No eligible model fits this conversation and the estimated spending limit. Shorten the conversation.', attempts)
    async with httpx.AsyncClient() as client:
        for index, candidate in enumerate(selected):
            remaining = TOTAL_BUDGET_SECONDS - (monotonic() - started)
            if remaining <= 0:
                break
            if candidate.is_free and (skip_free or (remaining <= PER_ATTEMPT_SECONDS + 1 and any(not m.is_free for m in selected[index + 1:]))):
                continue
            bound = estimate(candidate, tokens, configured_output)
            if reserved + bound > budget:
                continue
            reserved += bound  # Failures/timeouts are not proof of zero billing.
            attempt = Attempt(model=candidate.id, status=0, reason='unavailable', is_paid=not candidate.is_free,
                              estimated_cost_usd=format(bound, 'f'))
            attempts.append(attempt)
            timeout = min(PER_ATTEMPT_SECONDS, remaining)
            payload = {'model': candidate.id, 'messages': messages, 'stream': False,
                       'max_tokens': output_limit(candidate, configured_output), 'provider': provider_limits(candidate)}
            if candidate.supports_reasoning:
                payload['reasoning'] = {'enabled': False}
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
                cost = reported_cost(data)
                if cost is not None:
                    attempt.actual_cost_usd = format(cost, 'f')
                    reserved += max(Decimal('0'), cost - bound)
                error = data.get('error') if isinstance(data.get('error'), dict) else {}
                status = response.status_code
                if status == 200 and not error:
                    try:
                        answer = data['choices'][0]['message']['content']
                    except (KeyError, IndexError, TypeError):
                        answer = None
                    if isinstance(answer, str) and answer.strip():
                        attempt.status, attempt.reason = 200, 'answered'
                        reported_model = data.get('model')
                        actual_model = reported_model.strip() if isinstance(reported_model, str) else ''
                        known = [Decimal(a.actual_cost_usd) for a in attempts if a.actual_cost_usd is not None]
                        actual_total = sum(known, Decimal('0')) if known and not any(a.is_paid and a.actual_cost_usd is None for a in attempts) else None
                        return {'content': answer.strip(), 'model': actual_model or candidate.id,
                                'used_model': candidate.id, 'attempts': attempts,
                                'fallback_used': len(attempts) > 1, 'is_paid': not candidate.is_free,
                                'estimated_cost_usd': format(reserved, 'f'),
                                'actual_cost_usd': format(actual_total, 'f') if actual_total is not None else None,
                                'budget_usd': format(budget, 'f')}
                    attempt.status, attempt.reason = 502, 'empty_reply'
                else:
                    if status == 200:
                        try: status = int(error.get('code', 502))
                        except (ValueError, TypeError): status = 502
                    retry, reason = error_policy(status, error)
                    attempt.status, attempt.reason = status, reason
                    if reason == 'free_limit' and candidate.is_free:
                        skip_free = True
                    delay = retry_delay(response.headers.get('Retry-After'))
                    if skip_free:
                        delay = 0  # A free-only quota does not apply to the authorized paid request.
                    if not retry:
                        descriptions = {
                            401: 'The service key was rejected. Update the server configuration.',
                            402: 'OpenRouter rejected the account credit or key spending limit. No further requests were sent.',
                            403: 'The provider rejected the request under its policies or account settings.',
                            429: 'The account-wide request limit is reached. Try again later.',
                        }
                        failed(status if status in (400, 401, 402, 403, 404, 422, 429) else 503,
                            descriptions.get(status, 'The provider could not accept this request. Your draft is saved locally.'), attempts, delay)
            except (httpx.TimeoutException, asyncio.TimeoutError):
                attempt.status, attempt.reason = 504, 'timeout'
            except httpx.HTTPError:
                attempt.status, attempt.reason = 502, 'network_error'
            if attempt.is_paid:
                break  # Cheapest mode never risks a second paid attempt, even after a timeout.
            if index + 1 < len(selected):
                remaining = TOTAL_BUDGET_SECONDS - (monotonic() - started)
                if delay >= remaining and delay > 0:
                    failed(429, 'The provider asks you to wait before retrying. Your draft is saved locally.', attempts, delay)
                await asyncio.sleep(min(max(.15, delay), max(0, remaining)))
    failed(503, f'No response was available after {len(attempts)} eligible model attempts. Your draft is saved locally.', attempts)


complete_free = complete_with_fallback  # Historical import compatibility; policy is no longer free-only.