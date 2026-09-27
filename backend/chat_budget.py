"""Conservative estimates, NOT an OpenRouter-enforced per-request billing cap."""
import math
import os
from decimal import Decimal

from fastapi import HTTPException
from free_models import ModelOption, nonnegative_price


def settings() -> tuple[Decimal, int]:
    try:
        budget = nonnegative_price(os.environ['OPENROUTER_REQUEST_BUDGET_USD'])
        output = int(os.environ['OPENROUTER_MAX_OUTPUT_TOKENS'])
        if budget is None or budget > 1 or not 128 <= output <= 3200:
            raise ValueError('Invalid budget')
        return budget, output
    except (KeyError, ValueError, TypeError):
        raise HTTPException(503, 'The request budget or output limit is not configured correctly.')


def prompt_bound(messages: list[dict]) -> int:
    # UTF-8 bytes plus a safety margin and message framing, not characters / 4.
    return math.ceil(sum(len(message['content'].encode('utf-8')) for message in messages) * 1.25) + 128 + 32 * len(messages)


def output_limit(model: ModelOption, configured: int) -> int:
    return min(configured, model.max_completion_tokens or configured)


def estimate(model: ModelOption, prompt_tokens: int, configured: int) -> Decimal:
    return Decimal(model.prompt_price) * prompt_tokens + Decimal(model.completion_price) * output_limit(model, configured)


def provider_limits(model: ModelOption) -> dict:
    return {'sort': 'price', 'allow_fallbacks': False, 'require_parameters': True,
        'max_price': {'prompt': float(Decimal(model.prompt_price) * 1000000),
                      'completion': float(Decimal(model.completion_price) * 1000000), 'request': 0}}


def reported_cost(data: dict) -> Decimal | None:
    usage = data.get('usage')
    return nonnegative_price(usage.get('cost')) if isinstance(usage, dict) else None