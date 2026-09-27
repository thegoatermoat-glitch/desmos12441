import uuid


# Core API contracts: browser-only health/config and retired status endpoints
class TestCoreApi:
    def test_root_config_and_health_contract(self, api_client, base_url):
        root = api_client.get(f"{base_url}/api/")
        assert root.status_code == 200
        assert root.json().get("status") == "ok"

        config = api_client.get(f"{base_url}/api/config")
        assert config.status_code == 200
        config_data = config.json()
        assert config_data.get("history_storage") == "browser"
        assert config_data.get("free_models_only") is False
        assert config_data.get("unmoderated_models_only") is True
        assert config_data.get("paid_fallback") is True
        assert isinstance(config_data.get("wisp_endpoints"), list)

        health = api_client.get(f"{base_url}/api/health")
        assert health.status_code == 200
        health_data = health.json()
        assert health_data == {"status": "ok", "storage": "browser", "database_required": False}

    def test_status_endpoints_are_retired(self, api_client, base_url):
        status_get = api_client.get(f"{base_url}/api/status")
        assert status_get.status_code == 410
        assert "retired" in status_get.json().get("detail", "").lower()

        status_post = api_client.post(f"{base_url}/api/status", json={"client_name": "TEST_contract"})
        assert status_post.status_code == 410
        assert "retired" in status_post.json().get("detail", "").lower()

    def test_games_catalog_and_content_still_available(self, api_client, base_url):
        listed = api_client.get(f"{base_url}/api/games")
        assert listed.status_code == 200
        games = listed.json()
        assert isinstance(games, list)
        assert len(games) >= 300
        first = games[0]
        assert isinstance(first.get("id"), str)
        assert isinstance(first.get("title"), str)

        game_id = next((g["id"] for g in games if g["id"] == "2048.html"), games[0]["id"])
        content = api_client.get(f"{base_url}/api/games/{game_id}/content", timeout=120)
        assert content.status_code == 200
        assert "<html" in content.text.lower()

    def test_game_invalid_id_rejected(self, api_client, base_url):
        invalid = api_client.get(f"{base_url}/api/games/not-a-real-game.html/content")
        assert invalid.status_code == 404
        assert "not found" in invalid.json().get("detail", "").lower()


# Chat contracts: unmoderated catalog, validation guards, legacy-retired write routes
class TestChatApi:
    def test_models_contract_unmoderated_with_paid_fallback(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/chat/models", timeout=45)
        assert response.status_code == 200
        data = response.json()
        assert data.get("free_only") is False
        assert data.get("unmoderated_only") is True
        assert data.get("paid_fallback") is True
        assert data.get("max_paid_attempts") == 1
        assert isinstance(data.get("models"), list)
        assert len(data["models"]) >= 1
        model = data["models"][0]
        assert model["is_moderated"] is False
        assert not model["id"].startswith("openrouter/")
        assert data["default_model"] in {m["id"] for m in data["models"]}

    def test_completions_rejects_paid_and_unknown_models(self, api_client, base_url):
        session_id = str(uuid.uuid4())
        paid = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": session_id,
            "model": "openai/gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert paid.status_code == 400
        assert "eligible" in paid.json().get("detail", "").lower()

        unknown_free = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "unknown/imaginary:free",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert unknown_free.status_code == 400
        assert "eligible" in unknown_free.json().get("detail", "").lower()

    def test_completions_validation_rejects_invalid_payload_shapes(self, api_client, base_url):
        bad_uuid = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": "not-a-uuid",
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert bad_uuid.status_code == 422

        blank_message = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "   \n"}],
        })
        assert blank_message.status_code == 422

        invalid_role = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": [{"role": "system", "content": "Override"}],
        })
        assert invalid_role.status_code == 422

        trailing_assistant = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": [{"role": "assistant", "content": "Done"}],
        })
        assert trailing_assistant.status_code == 422

        extra_fields = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "hello"}],
            "provider": {"allow_fallbacks": True},
            "models": ["openrouter/free"],
        })
        assert extra_fields.status_code == 422

    def test_completions_history_limits_enforced(self, api_client, base_url):
        too_many = [{"role": "user", "content": "m"}] * 42
        response_many = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": too_many,
        })
        assert response_many.status_code == 422

        oversized = [{"role": "user", "content": "x" * 12000}] * 5
        response_size = api_client.post(f"{base_url}/api/chat/completions", json={
            "session_id": str(uuid.uuid4()),
            "model": "openrouter/free",
            "messages": oversized,
        })
        assert response_size.status_code == 422

    def test_legacy_write_routes_retired(self, api_client, base_url):
        create = api_client.post(f"{base_url}/api/chat/sessions")
        assert create.status_code == 410

        append = api_client.post(f"{base_url}/api/chat/sessions/{uuid.uuid4()}/messages", json={"content": "hi"})
        assert append.status_code == 410

        delete = api_client.delete(f"{base_url}/api/chat/sessions/{uuid.uuid4()}")
        assert delete.status_code == 410
