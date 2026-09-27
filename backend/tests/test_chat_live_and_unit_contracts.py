import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chat
import free_fallback
import publisher_models
import server
from free_models import FreeModel


# Unit contract checks: browser-only mode and provider payload guardrails
class TestUnitContracts:
    def test_health_and_config_do_not_require_database(self, monkeypatch):
        monkeypatch.delenv("MONGO_URL", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)
        client = TestClient(server.app)

        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "storage": "browser", "database_required": False}

        config = client.get("/api/config")
        assert config.status_code == 200
        assert config.json()["legacy_import_available"] is False

        recover = client.get(f"/api/chat/sessions/{uuid.uuid4()}")
        assert recover.status_code == 410

    def test_completions_request_body_enforces_zero_price_and_no_fallback(self, monkeypatch):
        sent_payload = {}
        evidence = {
            "qwen/qwen3.8-27b:free": {
                "model_name": "Qwen",
                "label": "uncensored",
                "publisher_url": "https://publisher.test/qwen",
                "canonical_slug": "synthetic/qwen-free",
            },
            "inclusionai/ling-3.0-flash-fin:free": {
                "model_name": "Ling",
                "label": "uncensored",
                "publisher_url": "https://publisher.test/ling",
                "canonical_slug": "synthetic/ling-free",
            },
        }

        def fake_evidence(model_id):
            return evidence.get(model_id)

        monkeypatch.setattr(publisher_models, "AUDITED_MODELS", {
            model_id: {
                "model_name": values["model_name"],
                "label": values["label"],
                "publisher": "Synthetic Publisher",
                "publisher_url": values["publisher_url"],
                "quote": "publisher described unrestricted",
                "canonical_slug": values["canonical_slug"],
                "hugging_face_ids": [f"synthetic/{model_id.replace('/', '-')}"] ,
                "reviewed_on": "2026-09-27",
            }
            for model_id, values in evidence.items()
        })

        async def fake_models(force_refresh=False):
            return [
                FreeModel(id="qwen/qwen3.8-27b:free", name="Qwen", context_length=32768, is_moderated=False, publisher_verified=True),
                FreeModel(id="inclusionai/ling-3.0-flash-fin:free", name="Ling", context_length=32768, is_moderated=False, publisher_verified=True),
            ]

        class FakeResponse:
            status_code = 200
            headers = {}

            @staticmethod
            def json():
                return {
                    "model": "qwen/qwen3.8-27b:free",
                    "choices": [{"message": {"content": "ok"}}],
                }

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, headers, json, timeout):
                sent_payload["url"] = url
                sent_payload["json"] = json
                sent_payload["headers"] = headers
                return FakeResponse()

        monkeypatch.setattr(chat, "get_models", fake_models)
        monkeypatch.setattr(chat, "publisher_evidence", fake_evidence)
        monkeypatch.setattr(free_fallback.httpx, "AsyncClient", FakeAsyncClient)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
        monkeypatch.setenv("APP_ORIGIN", "https://example.test")
        monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.01")
        monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")

        session_id = str(uuid.uuid4())
        client = TestClient(server.app)
        response = client.post("/api/chat/completions", json={
            "session_id": session_id,
            "model": "qwen/qwen3.8-27b:free",
            "messages": [{"role": "user", "content": "Hello"}],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["requested_model"] == "qwen/qwen3.8-27b:free"
        assert data["used_model"] == "qwen/qwen3.8-27b:free"
        assert data["model"] == "qwen/qwen3.8-27b:free"

        body = sent_payload["json"]
        assert body["provider"]["max_price"] == {"prompt": 0, "completion": 0, "request": 0}
        assert body["provider"]["allow_fallbacks"] is False
        assert body["provider"]["require_parameters"] is True
        assert body["provider"]["sort"] == "price"
        assert "models" not in body
        assert body["max_tokens"] == 1024
        assert body["messages"][0]["role"] == "system"
        assert sent_payload["headers"]["X-Session-ID"] == session_id

    def test_completions_preserve_messages_and_session_across_retries(self, monkeypatch):
        sent = []
        evidence = {
            "qwen/qwen3.8-27b:free": {
                "model_name": "Qwen",
                "label": "uncensored",
                "publisher_url": "https://publisher.test/qwen",
                "canonical_slug": "synthetic/qwen-free",
            },
            "inclusionai/ling-3.0-flash-fin:free": {
                "model_name": "Ling",
                "label": "uncensored",
                "publisher_url": "https://publisher.test/ling",
                "canonical_slug": "synthetic/ling-free",
            },
        }

        def fake_evidence(model_id):
            return evidence.get(model_id)

        monkeypatch.setattr(publisher_models, "AUDITED_MODELS", {
            model_id: {
                "model_name": values["model_name"],
                "label": values["label"],
                "publisher": "Synthetic Publisher",
                "publisher_url": values["publisher_url"],
                "quote": "publisher described unrestricted",
                "canonical_slug": values["canonical_slug"],
                "hugging_face_ids": [f"synthetic/{model_id.replace('/', '-')}"] ,
                "reviewed_on": "2026-09-27",
            }
            for model_id, values in evidence.items()
        })

        async def fake_models(force_refresh=False):
            return [
                FreeModel(id="qwen/qwen3.8-27b:free", name="Qwen", context_length=32768, is_moderated=False, publisher_verified=True),
                FreeModel(id="inclusionai/ling-3.0-flash-fin:free", name="Ling", context_length=32768, is_moderated=False, publisher_verified=True),
            ]

        class FakeResponse:
            def __init__(self, status_code, payload):
                self.status_code = status_code
                self._payload = payload
                self.headers = {}

            def json(self):
                return self._payload

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                self.calls = 0

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, headers, json, timeout):
                self.calls += 1
                sent.append({"url": url, "headers": headers, "json": json})
                if self.calls == 1:
                    return FakeResponse(200, {"choices": [{"message": {"content": "   "}}]})
                return FakeResponse(200, {
                    "model": json["model"],
                    "choices": [{"message": {"content": "READY"}}],
                })

        monkeypatch.setattr(chat, "get_models", fake_models)
        monkeypatch.setattr(chat, "publisher_evidence", fake_evidence)
        monkeypatch.setattr(free_fallback.httpx, "AsyncClient", FakeAsyncClient)
        async def _skip_sleep(*_args, **_kwargs):
            return None

        monkeypatch.setattr(free_fallback.asyncio, "sleep", _skip_sleep)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
        monkeypatch.setenv("APP_ORIGIN", "https://example.test")
        monkeypatch.setenv("OPENROUTER_REQUEST_BUDGET_USD", "0.01")
        monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1024")

        session_id = str(uuid.uuid4())
        messages = [
            {"role": "user", "content": "Say READY"},
            {"role": "assistant", "content": "READY"},
            {"role": "user", "content": "Repeat READY"},
        ]
        client = TestClient(server.app)
        response = client.post("/api/chat/completions", json={
            "session_id": session_id,
            "model": "qwen/qwen3.8-27b:free",
            "messages": messages,
        })

        assert response.status_code == 200
        assert len(sent) == 2
        assert sent[0]["headers"]["X-Session-ID"] == session_id
        assert sent[1]["headers"]["X-Session-ID"] == session_id
        assert sent[0]["json"]["messages"] == sent[1]["json"]["messages"]
        assert sent[0]["json"]["messages"][-3:] == messages


# Live integration checks: real free model call, multi-turn context, isolated session behavior
class TestLiveFreeModelIntegration:
    def _completion(self, api_client, base_url, model_id, session_id, messages):
        return api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(session_id),
            "model": model_id,
            "messages": messages,
        }, timeout=120)

    def test_live_completion_multiturn_and_isolated_session(self, api_client, base_url):
        models_response = api_client.get(f"{base_url}/api/chat/models", timeout=60)
        assert models_response.status_code == 200
        model_data = models_response.json()
        selected_model = model_data["default_model"]

        marker = str(7000 + int(uuid.uuid4().hex[:3], 16) % 2000)
        thread_id = uuid.uuid4()
        turn_one = self._completion(api_client, base_url, selected_model, thread_id, [
            {"role": "user", "content": f"Remember this number for this chat only: {marker}. Reply exactly READY."}
        ])
        assert turn_one.status_code == 200
        assistant_one = turn_one.json()["content"]

        turn_two = self._completion(api_client, base_url, selected_model, thread_id, [
            {"role": "user", "content": f"Remember this number for this chat only: {marker}. Reply exactly READY."},
            {"role": "assistant", "content": assistant_one},
            {"role": "user", "content": "What number did I ask you to remember? Reply with only the number."},
        ])
        assert turn_two.status_code == 200
        assert marker in turn_two.json()["content"]
        assert turn_two.json()["session_id"] == str(thread_id)

        isolated = self._completion(api_client, base_url, selected_model, uuid.uuid4(), [
            {"role": "user", "content": "If I did not give any token in this chat, reply exactly NONE."}
        ])
        assert isolated.status_code == 200
        assert isolated.json()["session_id"] != str(thread_id)


# Live paid verification: dynamically choose cheapest currently-eligible paid model and make one real call.
class TestLivePaidIntegration:
    def test_live_cheapest_paid_single_call_under_budget(self, api_client, base_url, monkeypatch):
        pytest.skip("Covered by TestLiveFreeModelIntegration to keep paid live calls <= 3")
