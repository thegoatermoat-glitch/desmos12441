import uuid

import pytest


# Core public API coverage: config, games, status checks, and chat session lifecycle
class TestCoreApi:
    def test_root_and_config(self, api_client, base_url):
        root = api_client.get(f"{base_url}/api/")
        assert root.status_code == 200
        root_data = root.json()
        assert root_data["status"] == "ok"

        config = api_client.get(f"{base_url}/api/config")
        assert config.status_code == 200
        config_data = config.json()
        assert isinstance(config_data.get("wisp_endpoints"), list)
        assert len(config_data["wisp_endpoints"]) >= 2
        assert isinstance(config_data.get("ai_model"), str)

    def test_status_create_and_persist(self, api_client, base_url):
        payload = {"client_name": "TEST_backend_pytest"}
        created = api_client.post(f"{base_url}/api/status", json=payload)
        assert created.status_code == 200
        created_data = created.json()
        assert created_data["client_name"] == payload["client_name"]
        assert isinstance(created_data["id"], str)

        listed = api_client.get(f"{base_url}/api/status")
        assert listed.status_code == 200
        listed_data = listed.json()
        assert any(item["id"] == created_data["id"] for item in listed_data)

    def test_games_catalog_count_and_required_titles(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/games")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 300
        ids = {game["id"] for game in data}
        assert "2048.html" in ids
        assert "google-dino.html" in ids

    def test_game_content_2048_and_dino(self, api_client, base_url):
        game_2048 = api_client.get(f"{base_url}/api/games/2048.html/content")
        assert game_2048.status_code == 200
        assert "<html" in game_2048.text.lower()

        dino = api_client.get(f"{base_url}/api/games/google-dino.html/content")
        assert dino.status_code == 200
        assert "<html" in dino.text.lower()

    def test_game_invalid_and_path_traversal_rejected(self, api_client, base_url):
        invalid = api_client.get(f"{base_url}/api/games/not-a-real-game.html/content")
        assert invalid.status_code == 404

        traversal = api_client.get(f"{base_url}/api/games/..%2F..%2Fetc%2Fpasswd/content")
        assert traversal.status_code == 404


# Chat API coverage: UUID validation, whitespace handling, session persistence, multi-turn behavior
class TestChatApi:
    def test_chat_session_create_get_delete(self, api_client, base_url):
        created = api_client.post(f"{base_url}/api/chat/sessions")
        assert created.status_code == 201
        session = created.json()
        session_id = session["id"]
        assert isinstance(session_id, str)

        fetched = api_client.get(f"{base_url}/api/chat/sessions/{session_id}")
        assert fetched.status_code == 200
        fetched_data = fetched.json()
        assert fetched_data["id"] == session_id
        assert fetched_data["messages"] == []

        deleted = api_client.delete(f"{base_url}/api/chat/sessions/{session_id}")
        assert deleted.status_code == 204

        after_delete = api_client.get(f"{base_url}/api/chat/sessions/{session_id}")
        assert after_delete.status_code == 404

    def test_chat_invalid_uuid_and_whitespace(self, api_client, base_url):
        invalid = "not-a-uuid"
        fetched = api_client.get(f"{base_url}/api/chat/sessions/{invalid}")
        assert fetched.status_code == 404

        created = api_client.post(f"{base_url}/api/chat/sessions")
        assert created.status_code == 201
        session_id = created.json()["id"]

        whitespace = api_client.post(
            f"{base_url}/api/chat/sessions/{session_id}/messages",
            json={"content": "   \n\t  "},
        )
        assert whitespace.status_code == 422

        delete_invalid = api_client.delete(f"{base_url}/api/chat/sessions/{invalid}")
        assert delete_invalid.status_code == 404

    def test_chat_two_turn_context_and_persistence(self, api_client, base_url):
        created = api_client.post(f"{base_url}/api/chat/sessions")
        assert created.status_code == 201
        session_id = created.json()["id"]
        marker = f"ORBIT-{uuid.uuid4().hex[:6]}"

        first_turn = api_client.post(
            f"{base_url}/api/chat/sessions/{session_id}/messages",
            json={"content": f"Reply with exactly this token: {marker}"},
            timeout=120,
        )
        if first_turn.status_code != 200:
            pytest.skip(f"OpenRouter unavailable for first turn (status {first_turn.status_code})")
        first_data = first_turn.json()
        assert first_data["id"] == session_id
        assert len(first_data["messages"]) >= 2

        second_turn = api_client.post(
            f"{base_url}/api/chat/sessions/{session_id}/messages",
            json={"content": "What token did I ask you to reply with? Give only the token."},
            timeout=120,
        )
        if second_turn.status_code != 200:
            pytest.skip(f"OpenRouter unavailable for second turn (status {second_turn.status_code})")
        second_data = second_turn.json()
        assert len(second_data["messages"]) >= 4

        last_answer = second_data["messages"][-1]["content"]
        assert marker.lower() in last_answer.lower()

        fetched = api_client.get(f"{base_url}/api/chat/sessions/{session_id}")
        assert fetched.status_code == 200
        fetched_data = fetched.json()
        assert fetched_data["id"] == session_id
        assert len(fetched_data["messages"]) >= 4
