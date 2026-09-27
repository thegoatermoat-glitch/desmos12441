import sys
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import free_fallback
import free_models
import publisher_models
from free_models import FreeModel


# Catalogue + fallback contract tests for strict unmoderated filtering and cheapest paid fallback rules.
def _model(model_id: str, *, name: str | None = None, prompt="0", completion="0", request="0", context=8192):
    return FreeModel(
        id=model_id,
        name=name or model_id,
        context_length=context,
        is_moderated=False,
        prompt_price=str(prompt),
        completion_price=str(completion),
        request_price=str(request),
        publisher_verified=True,
        publisher_label="uncensored",
        publisher_model_name=name or model_id,
        publisher_url="https://publisher.test/model",
        publisher_quote="publisher described unrestricted",
        publisher_reviewed_on="2026-09-27",
    )


def _set_audited(monkeypatch, model_ids):
    monkeypatch.setattr(publisher_models, "AUDITED_MODELS", {
        model_id: {
            "model_name": f"Model {model_id}",
            "label": "uncensored",
            "publisher": "Synthetic Publisher",
            "publisher_url": f"https://publisher.test/{model_id.replace('/', '-')}",
            "quote": "publisher described unrestricted",
            "canonical_slug": f"canonical/{model_id.replace('/', '-')}",
            "hugging_face_ids": [f"synthetic/{model_id.replace('/', '-')}"] ,
            "reviewed_on": "2026-09-27",
        }
        for model_id in model_ids
    })


class _FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._payload


def _fake_async_client_factory(events, recorder):
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._events = list(events)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers, json, timeout):
            recorder.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
            event = self._events.pop(0)
            if isinstance(event, Exception):
                raise event
            return event

    return _FakeAsyncClient


def test_candidates_free_first_then_single_cheapest_paid(monkeypatch):
    monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.01")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")
    models = [
        _model("a/selected-free", name="A Free"),
        _model("b/other-free", name="B Free"),
        _model("c/other-free", name="C Free"),
        _model("d/other-free", name="D Free"),
        _model("e/other-free", name="E Free"),
        _model("paid/cheapest", name="Paid Cheapest", prompt="0.000000001", completion="0.000000001"),
        _model("paid/expensive", name="Paid Expensive", prompt="0.0000001", completion="0.0000001"),
    ]
    _set_audited(monkeypatch, [m.id for m in models])
    messages = [{"role": "user", "content": "hello"}]

    picked = free_fallback.candidates("a/selected-free", models, messages)
    ids = [m.id for m in picked]

    assert len(ids) <= 5
    assert ids[0] == "a/selected-free"
    assert ids[-1] == "paid/cheapest"
    assert ids.count("paid/cheapest") == 1
    assert "paid/expensive" not in ids


def test_candidates_zero_budget_forbids_paid(monkeypatch):
    monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")
    models = [
        _model("a/selected-free"),
        _model("b/free"),
        _model("paid/eligible", prompt="0.000000001", completion="0.000000001"),
    ]
    _set_audited(monkeypatch, [m.id for m in models])

    picked = free_fallback.candidates("a/selected-free", models, [{"role": "user", "content": "hi"}])
    assert all(model.is_free for model in picked)


@pytest.mark.anyio
async def test_complete_with_fallback_uses_one_paid_attempt_max(monkeypatch):
    monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.01")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")
    recorded = []
    events = [
        _FakeResponse(429, {"error": {"message": "free-models-per-day", "metadata": {"quota_scope": "free"}}}),
        _FakeResponse(200, {
            "model": "paid/cheapest",
            "usage": {"cost": "0.0002"},
            "choices": [{"message": {"content": "READY"}}],
        }),
    ]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))

    async def _skip_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(free_fallback.asyncio, "sleep", _skip_sleep)
    models = [
        _model("a/free"),
        _model("b/free"),
        _model("paid/cheapest", prompt="0.000000001", completion="0.000000001"),
    ]
    _set_audited(monkeypatch, [m.id for m in models])

    result = await free_fallback.complete_with_fallback(
        "https://openrouter.ai/api/v1/chat/completions",
        {"X-Session-ID": "s", "Authorization": "Bearer x"},
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        "a/free",
        models,
        started=free_fallback.monotonic(),
    )

    assert result["content"] == "READY"
    assert result["is_paid"] is True
    assert len([a for a in result["attempts"] if a.is_paid]) == 1
    assert all(call["json"]["provider"]["allow_fallbacks"] is False for call in recorded)
    assert all(call["json"]["provider"]["require_parameters"] is True for call in recorded)
    assert all(call["json"]["provider"]["max_price"]["request"] == 0 for call in recorded)
    assert all(call["json"]["max_tokens"] == 1024 for call in recorded)


def test_parse_catalogue_strict_filters_and_price_validation(monkeypatch):
    rows = [
        {
            "id": "ok/free-model",
            "name": "Allowed",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0", "input_cache_read": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False, "max_completion_tokens": 700},
            "supported_parameters": ["max_tokens", "temperature"],
        },
        {
            "id": "bad/moderated",
            "name": "Moderated",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": True},
            "supported_parameters": ["max_tokens"],
        },
        {
            "id": "bad/unknown-mod-flag",
            "name": "Unknown",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": None},
            "supported_parameters": ["max_tokens"],
        },
        {
            "id": "bad/request-fee",
            "name": "Request fee",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0.001"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
            "supported_parameters": ["max_tokens"],
        },
        {
            "id": "bad/missing-prompt",
            "name": "No prompt",
            "context_length": 4096,
            "pricing": {"completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
            "supported_parameters": ["max_tokens"],
        },
        {
            "id": "bad/no-max-tokens",
            "name": "No max_tokens",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
            "supported_parameters": ["temperature"],
        },
        {
            "id": "bad/openrouter/router",
            "name": "Router",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
            "supported_parameters": ["max_tokens"],
        },
    ]

    rows[-1]["id"] = "openrouter/router-model"
    _set_audited(monkeypatch, [row["id"] for row in rows])
    rows[0]["canonical_slug"] = "canonical/ok-free-model"
    rows[0]["hugging_face_id"] = "synthetic/ok-free-model"
    for row in rows[1:]:
        row["canonical_slug"] = f"canonical/{row['id'].replace('/', '-')}"
        row["hugging_face_id"] = f"synthetic/{row['id'].replace('/', '-')}"

    parsed = free_models.parse_catalogue(rows)
    ids = [m.id for m in parsed]

    assert ids == ["ok/free-model"]
    assert parsed[0].is_moderated is False
    assert parsed[0].max_completion_tokens == 700


@pytest.mark.anyio
async def test_get_models_malformed_upstream_is_sanitized(monkeypatch):
    class BadResponse:
        def raise_for_status(self):
            return None

        @staticmethod
        def json():
            return {"unexpected": "shape"}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, endpoint):
            return BadResponse()

    monkeypatch.setenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
    monkeypatch.setattr(free_models.httpx, "AsyncClient", lambda timeout=15: FakeAsyncClient())
    monkeypatch.setattr(free_models, "_models", [])
    monkeypatch.setattr(free_models, "_expires", 0.0)

    with pytest.raises(HTTPException) as failure:
        await free_models.get_models(force_refresh=True)

    assert failure.value.status_code == 503
    assert failure.value.detail == "The eligible model list is unavailable. Please try again."
    assert "key" not in failure.value.detail.lower()


def test_retry_delay_parses_finite_and_nonfinite():
    assert free_fallback.retry_delay("2.4") == pytest.approx(2.4)
    assert free_fallback.retry_delay("nan") == 0
    assert free_fallback.retry_delay("inf") == 0
    assert free_fallback.retry_delay("not-a-date") == 0
    assert free_fallback.retry_delay("Wed, 21 Oct 2030 07:28:00 GMT") >= 0


@pytest.mark.parametrize("flag", [True, None, "false", 0, 1, "unknown"])
def test_catalogue_never_coerces_moderation_metadata(flag):
    row = {"id": "author/text", "name": "Text", "context_length": 8192,
           "pricing": {"prompt": "0", "completion": "0"},
           "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
           "top_provider": {"is_moderated": flag}, "supported_parameters": ["max_tokens"]}
    assert free_models.parse_catalogue([row]) == []


@pytest.mark.parametrize("price", [None, "-1", "NaN", "Infinity", "invalid"])
def test_catalogue_rejects_unknown_or_unbounded_cost(price):
    row = {"id": "author/text", "context_length": 8192,
           "pricing": {"prompt": price, "completion": "0"},
           "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
           "top_provider": {"is_moderated": False}, "supported_parameters": ["max_tokens"]}
    assert free_models.parse_catalogue([row]) == []


def test_malformed_input_modalities_are_excluded_without_crash():
    row = {"id": "author/text", "context_length": 8192,
           "pricing": {"prompt": "0", "completion": "0"},
           "architecture": {"input_modalities": 123, "output_modalities": ["text"]},
           "top_provider": {"is_moderated": False}, "supported_parameters": ["max_tokens"]}
    assert free_models.parse_catalogue([row]) == []


@pytest.mark.anyio
@pytest.mark.parametrize("paid_event", [httpx.ReadTimeout("timed out"),
    _FakeResponse(200, {"choices": []}), _FakeResponse(503, {"error": {"message": "unavailable"}})])
async def test_paid_failure_never_triggers_a_second_paid_request(monkeypatch, paid_event):
    monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.01")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")
    calls = []
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory([paid_event], calls))
    first = _model("paid/low", prompt="0.00000001", completion="0.00000001")
    second = _model("paid/high", prompt="0.0000001", completion="0.0000001")
    _set_audited(monkeypatch, [first.id, second.id])
    with pytest.raises(HTTPException) as failure:
        await free_fallback.complete_with_fallback("https://provider.test/completions", {},
            [{"role": "user", "content": "Hi"}], first.id, [second, first], free_fallback.monotonic())
    assert len(calls) == 1
    assert calls[0]["json"]["model"] == first.id
    assert failure.value.detail["paid_attempted"] is True
    assert "may have incurred a charge" in failure.value.detail["message"]


def test_unicode_context_and_budget_checks_are_conservative(monkeypatch):
    from chat_budget import prompt_bound
    monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.000001")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")
    messages = [{"role": "user", "content": "漢🙂" * 300}]
    assert prompt_bound(messages) > len(messages[0]["content"].encode("utf-8"))
    model = _model("paid/low", prompt="0.00000001", completion="0.00000001")
    _set_audited(monkeypatch, [model.id])
    assert free_fallback.candidates(model.id, [model], messages) == []
