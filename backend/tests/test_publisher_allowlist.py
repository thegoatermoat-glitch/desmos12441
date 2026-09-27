"""Publisher-policy guards; all provider responses here are deterministic fixtures."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from free_models import ModelOption, parse_catalogue
import free_models
import free_fallback
from publisher_models import AUDITED_MODELS, verified_response_model

MODEL_ID = 'cognitivecomputations/dolphin-mistral-24b-venice-edition'


def row():
    proof = AUDITED_MODELS[MODEL_ID]
    return {'id': MODEL_ID, 'name': 'Venice: Uncensored', 'context_length': 128000,
            'canonical_slug': proof['canonical_slug'], 'hugging_face_id': proof['hugging_face_ids'][0],
            'pricing': {'prompt': '0.0000002', 'completion': '0.0000009'},
            'top_provider': {'is_moderated': False, 'max_completion_tokens': 8192},
            'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']},
            'supported_parameters': ['max_tokens']}


def test_actual_audit_preserves_publisher_evidence():
    parsed = parse_catalogue([row()])
    assert len(parsed) == 1
    assert parsed[0].publisher_verified is True
    assert parsed[0].publisher_url == AUDITED_MODELS[MODEL_ID]['publisher_url']
    assert 'most uncensored version' in parsed[0].publisher_quote
    assert parsed[0].is_free is False


@pytest.mark.parametrize('model_id', [MODEL_ID + ':free', 'thedrummer/cydonia-24b-v4.1',
    'qwen/qwen3.8-27b:free', 'openai/gpt-4o', 'openrouter/free'])
def test_names_and_provider_flags_cannot_expand_allowlist(model_id):
    item = row()
    item.update(id=model_id, name='Uncensored unrestricted Dolphin', description='Uncensored model')
    assert parse_catalogue([item]) == []


@pytest.mark.parametrize('field,value', [('canonical_slug', 'ordinary/model'),
    ('canonical_slug', None), ('hugging_face_id', 'someone/other-model'), ('hugging_face_id', None)])
def test_exact_id_with_changed_publisher_identity_is_not_eligible(field, value):
    item = row(); item[field] = value
    assert parse_catalogue([item]) == []


@pytest.mark.parametrize('flag', [True, None, 'false', 0])
def test_audited_model_still_requires_exact_false_moderation(flag):
    item = row(); item['top_provider']['is_moderated'] = flag
    assert parse_catalogue([item]) == []


@pytest.mark.parametrize('price', [None, '-1', 'NaN', 'Infinity'])
def test_audited_model_still_requires_known_prices(price):
    item = row(); item['pricing']['prompt'] = price
    assert parse_catalogue([item]) == []


def test_injected_ordinary_free_model_cannot_enter_fallback(monkeypatch):
    monkeypatch.setenv('OPENROUTER_REQUEST_BUDGET_USD', '0.01')
    monkeypatch.setenv('OPENROUTER_MAX_OUTPUT_TOKENS', '1024')
    approved = parse_catalogue([row()])[0]
    ordinary = ModelOption(id='ordinary/free-model', name='Uncensored', context_length=128000,
                           is_moderated=False, publisher_verified=True)
    picked = free_fallback.candidates(MODEL_ID, [ordinary, approved], [{'role': 'user', 'content': 'Hi'}])
    assert [model.id for model in picked] == [MODEL_ID]


@pytest.mark.anyio
@pytest.mark.parametrize('reported', [None, '', 'ordinary/model', MODEL_ID + ':free'])
async def test_unverified_response_is_not_returned_or_retried(monkeypatch, reported):
    monkeypatch.setenv('OPENROUTER_REQUEST_BUDGET_USD', '0.01')
    monkeypatch.setenv('OPENROUTER_MAX_OUTPUT_TOKENS', '1024')
    calls = []
    class Response:
        status_code, headers = 200, {}
        def json(self):
            return {'model': reported, 'usage': {'cost': '0.000001'},
                    'choices': [{'message': {'content': 'UNVERIFIED_CONTENT_MUST_NOT_LEAK'}}]}
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def post(self, *args, **kwargs): calls.append(kwargs); return Response()
    monkeypatch.setattr(free_fallback.httpx, 'AsyncClient', Client)
    with pytest.raises(HTTPException) as failure:
        await free_fallback.complete_with_fallback('https://provider.test/completions', {},
            [{'role': 'user', 'content': 'Hi'}], MODEL_ID, parse_catalogue([row()]), free_fallback.monotonic())
    assert len(calls) == 1
    assert failure.value.status_code == 502
    assert failure.value.detail['attempts'][0]['reason'] == 'unverified_model'
    assert 'UNVERIFIED_CONTENT_MUST_NOT_LEAK' not in str(failure.value.detail)


def test_only_audited_reported_aliases_are_accepted():
    assert verified_response_model(MODEL_ID, MODEL_ID)
    assert verified_response_model(MODEL_ID, AUDITED_MODELS[MODEL_ID]['canonical_slug'])
    assert not verified_response_model(MODEL_ID, 'other/dolphin')


@pytest.mark.anyio
async def test_no_eligible_live_model_fails_closed(monkeypatch):
    item = row(); item['id'] = 'ordinary/model'
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'data': [item]}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False
        async def get(self, url): return Response()
    monkeypatch.setenv('OPENROUTER_URL', 'https://provider.test/api/v1/chat/completions')
    monkeypatch.setattr(free_models.httpx, 'AsyncClient', Client)
    with pytest.raises(HTTPException) as failure:
        await free_models.get_models(force_refresh=True)
    assert failure.value.status_code == 503
    assert 'Ordinary-model fallback is disabled' in failure.value.detail