import asyncio
import math

import httpx
import pytest
from fastapi import HTTPException

import free_fallback
import free_models
from free_models import FreeModel


def _model(model_id: str, name: str | None = None, *, prompt="0", completion="0", request="0", moderated=None):
    return FreeModel(
        id=model_id,
        name=name or model_id,
        context_length=8192,
        is_moderated=moderated,
        prompt_price=str(prompt),
        completion_price=str(completion),
        request_price=str(request),
    )


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


@pytest.mark.anyio
async def test_candidates_prioritizes_selected_distinct_and_caps_at_five():
    # Fallback candidate policy: selected first, distinct IDs/families, maximum five zero-price free IDs.
    models = [
        _model("familya/model-a:free", "A"),
        _model("familya/model-a:free", "A duplicate"),
        _model("familya/model-b:free", "A second"),
        _model("familyb/model-1:free", "B1"),
        _model("familyc/model-1:free", "C1"),
        _model("familyd/model-1:free", "D1"),
        _model("familye/model-1:free", "E1"),
        _model("familyf/model-1:free", "F1"),
        _model("openai/gpt-4o", "Paid", prompt="1", completion="1"),
    ]

    selected = free_fallback.candidates("familya/model-a:free", models)
    ids = [m.id for m in selected]

    assert ids[0] == "familya/model-a:free"
    assert len(ids) == 5
    assert len(set(ids)) == 5
    assert "openai/gpt-4o" not in ids


@pytest.mark.anyio
async def test_complete_free_success_on_fifth_attempt_and_guardrails(monkeypatch):
    # Completion fallback flow: retries up to 5 with strict zero-price and no-provider-fallback payloads.
    recorded = []
    events = [
        _FakeResponse(500, {"error": {"message": "server error"}}),
        _FakeResponse(429, {"error": {"message": "per-model rate"}}),
        _FakeResponse(200, {"choices": [{"message": {"content": "   "}}]}),
        httpx.ReadTimeout("timeout"),
        _FakeResponse(200, {"model": "provider/reported-name", "choices": [{"message": {"content": "READY"}}]}),
    ]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))

    async def _skip_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(free_fallback.asyncio, "sleep", _skip_sleep)
    monkeypatch.setattr(free_fallback, "TOTAL_BUDGET_SECONDS", 55.0)
    monkeypatch.setattr(free_fallback, "PER_ATTEMPT_SECONDS", 12.0)

    models = [
        _model("qwen/qwen3.8-27b:free", "Qwen"),
        _model("inclusionai/ling-3.0-flash-fin:free", "Ling"),
        _model("google/gemini-2.0-flash-exp:free", "Gemini"),
        _model("meta-llama/llama-3.3-70b-instruct:free", "Llama"),
        _model("openrouter/free", "OpenRouter Free"),
    ]
    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "READY"}]

    result = await free_fallback.complete_free(
        "https://openrouter.ai/api/v1/chat/completions",
        {"X-Session-ID": "session-1", "Authorization": "Bearer test"},
        messages,
        "qwen/qwen3.8-27b:free",
        models,
        started=free_fallback.monotonic(),
    )

    assert result["content"] == "READY"
    assert result["model"] == "provider/reported-name"
    assert result["used_model"].endswith(":free") or result["used_model"] == "openrouter/free"
    assert result["fallback_used"] is True
    assert len(result["attempts"]) == 5

    assert len(recorded) == 5
    first_payload = recorded[0]["json"]
    for call in recorded:
        assert call["json"]["messages"] == messages
        assert call["json"]["provider"]["allow_fallbacks"] is False
        assert call["json"]["provider"]["require_parameters"] is True
        assert call["json"]["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
        assert call["json"]["max_tokens"] == 1200
        assert "models" not in call["json"]
        timeout_value = getattr(call["timeout"], "read", None)
        assert timeout_value is not None and float(timeout_value) <= 12.0
    assert first_payload["model"] == "qwen/qwen3.8-27b:free"


@pytest.mark.anyio
async def test_complete_free_exhaustion_stops_after_five_attempts(monkeypatch):
    # Exhaustion behavior: exactly 5 attempts then sanitized 503 failure.
    recorded = []
    events = [_FakeResponse(500, {"error": {"message": "upstream down"}}) for _ in range(5)]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))

    async def _skip_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(free_fallback.asyncio, "sleep", _skip_sleep)
    models = [_model(f"family{i}/model:free") for i in range(1, 7)]

    with pytest.raises(HTTPException) as failure:
        await free_fallback.complete_free(
            "https://openrouter.ai/api/v1/chat/completions",
            {"X-Session-ID": "session-x"},
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
            "family1/model:free",
            models,
            started=free_fallback.monotonic(),
        )

    assert failure.value.status_code == 503
    assert "No response was available after 5 free-model attempts" in failure.value.detail["message"]
    assert len(failure.value.detail["attempts"]) == 5
    assert len(recorded) == 5


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status,error_payload,expected_status,expected_reason",
    [
        (401, {"message": "bad key"}, 401, "account_error"),
        (402, {"message": "billing"}, 402, "account_error"),
        (403, {"message": "policy blocked"}, 403, "policy_error"),
        (429, {"message": "daily quota exceeded", "metadata": {"quota_scope": "account"}}, 429, "account_limit"),
        (404, {"message": "data policy violation"}, 404, "request_error"),
    ],
)
async def test_complete_free_non_retryable_statuses_stop_immediately(monkeypatch, status, error_payload, expected_status, expected_reason):
    # Error policy: account/policy/global-limit/privacy failures stop instead of rotating models.
    recorded = []
    events = [_FakeResponse(status, {"error": error_payload})]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))
    models = [_model("qwen/qwen3.8-27b:free"), _model("inclusionai/ling-3.0-flash-fin:free")]

    with pytest.raises(HTTPException) as failure:
        await free_fallback.complete_free(
            "https://openrouter.ai/api/v1/chat/completions",
            {"X-Session-ID": "s"},
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
            "qwen/qwen3.8-27b:free",
            models,
            started=free_fallback.monotonic(),
        )

    assert failure.value.status_code == expected_status
    assert failure.value.detail["attempts"][0]["reason"] == expected_reason
    assert len(recorded) == 1


@pytest.mark.anyio
async def test_complete_free_retries_provider_unavailable_404_then_succeeds(monkeypatch):
    # Model-specific unavailable 404 should retry other free models.
    recorded = []
    events = [
        _FakeResponse(404, {"error": {"message": "No endpoints found", "metadata": {"error_type": "provider_unavailable"}}}),
        _FakeResponse(200, {"model": "inclusionai/ling-3.0-flash-fin:free", "choices": [{"message": {"content": "ok"}}]}),
    ]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))

    async def _skip_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(free_fallback.asyncio, "sleep", _skip_sleep)
    models = [_model("qwen/qwen3.8-27b:free"), _model("inclusionai/ling-3.0-flash-fin:free")]
    result = await free_fallback.complete_free(
        "https://openrouter.ai/api/v1/chat/completions",
        {"X-Session-ID": "s"},
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        "qwen/qwen3.8-27b:free",
        models,
        started=free_fallback.monotonic(),
    )

    assert result["content"] == "ok"
    assert len(result["attempts"]) == 2
    assert result["attempts"][0].reason == "unavailable"


@pytest.mark.anyio
async def test_retry_after_budget_limit_returns_wait_error(monkeypatch):
    # Retry-After handling: long waits that exceed remaining budget should return immediate 429 with header.
    recorded = []
    events = [_FakeResponse(429, {"error": {"message": "per-model rate"}}, headers={"Retry-After": "9999"})]
    monkeypatch.setattr(free_fallback.httpx, "AsyncClient", _fake_async_client_factory(events, recorded))
    monkeypatch.setattr(free_fallback, "TOTAL_BUDGET_SECONDS", 1.0)
    monkeypatch.setattr(free_fallback, "PER_ATTEMPT_SECONDS", 1.0)

    times = iter([0.0, 0.2, 0.3])
    monkeypatch.setattr(free_fallback, "monotonic", lambda: next(times, 0.3))
    models = [_model("qwen/qwen3.8-27b:free"), _model("inclusionai/ling-3.0-flash-fin:free")]

    with pytest.raises(HTTPException) as failure:
        await free_fallback.complete_free(
            "https://openrouter.ai/api/v1/chat/completions",
            {"X-Session-ID": "s"},
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
            "qwen/qwen3.8-27b:free",
            models,
            started=0.0,
        )

    assert failure.value.status_code == 429
    assert failure.value.headers["Retry-After"] == str(math.ceil(9999))
    assert "wait" in failure.value.detail["message"].lower()


def test_retry_delay_parses_finite_nonfinite_and_http_date():
    # Retry-After parsing: finite seconds and date values only; non-finite values are ignored.
    assert free_fallback.retry_delay("2.4") == pytest.approx(2.4)
    assert free_fallback.retry_delay("nan") == 0
    assert free_fallback.retry_delay("inf") == 0
    assert free_fallback.retry_delay("not-a-date") == 0
    assert free_fallback.retry_delay("Wed, 21 Oct 2030 07:28:00 GMT") >= 0


def test_parse_catalogue_accepts_only_free_text_and_deduplicates():
    # Catalogue parsing: only free text output models, request price optional, duplicates removed.
    items = [
        {
            "id": "qwen/qwen3.8-27b:free",
            "name": "Qwen",
            "context_length": 100,
            "pricing": {"prompt": "0", "completion": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": True},
        },
        {
            "id": "qwen/qwen3.8-27b:free",
            "name": "Qwen duplicate",
            "context_length": 100,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": True},
        },
        {
            "id": "openrouter/free",
            "name": "OpenRouter",
            "context_length": 100,
            "pricing": {"prompt": "0", "completion": "0", "request": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
        },
        {
            "id": "paid/model",
            "name": "Paid",
            "context_length": 100,
            "pricing": {"prompt": "1", "completion": "0"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"is_moderated": False},
        },
    ]

    parsed = free_models.parse_catalogue(items)
    ids = [m.id for m in parsed]
    assert "qwen/qwen3.8-27b:free" in ids
    assert "openrouter/free" in ids
    assert ids.count("qwen/qwen3.8-27b:free") == 1
    assert "paid/model" not in ids


def test_parse_catalogue_rejects_nonzero_or_missing_required_prices_and_nontext():
    # Catalogue validation: non-zero/null/missing prompt/completion and non-text modalities are rejected.
    items = [
        {"id": "a:free", "pricing": {"prompt": "1", "completion": "0"}, "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
        {"id": "b:free", "pricing": {"prompt": "0", "completion": None}, "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
        {"id": "c:free", "pricing": {"prompt": "0"}, "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
        {"id": "d:free", "pricing": {"prompt": "0", "completion": "0", "request": "0"}, "architecture": {"input_modalities": ["image"], "output_modalities": ["text"]}},
        {"id": "e:free", "pricing": {"prompt": "0", "completion": "0", "request": "0.01"}, "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
    ]

    parsed = free_models.parse_catalogue(items)
    assert parsed == []


@pytest.mark.anyio
async def test_get_free_models_malformed_upstream_is_sanitized(monkeypatch):
    # Upstream model catalogue failures should return sanitized 503 without leaking internals/secrets.
    class BadResponse:
        def raise_for_status(self):
            return None

        @staticmethod
        def json():
            return {"unexpected": "shape"}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, endpoint):
            return BadResponse()

    monkeypatch.setenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
    monkeypatch.setattr(free_models.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(free_models, "_models", [])
    monkeypatch.setattr(free_models, "_expires", 0.0)

    with pytest.raises(HTTPException) as failure:
        await free_models.get_free_models()

    assert failure.value.status_code == 503
    assert failure.value.detail == "The free-model list is unavailable. Please try again."
    assert "key" not in failure.value.detail.lower()
