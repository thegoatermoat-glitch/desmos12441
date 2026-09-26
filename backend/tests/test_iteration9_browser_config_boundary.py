import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import app


# Iteration-9 browser rollout checks: live public config contract and content-host API boundary.
class TestIteration9BrowserConfigBoundary:
    def test_live_public_config_has_https_content_origin_and_shortcuts(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/config")
        assert response.status_code == 200

        data = response.json()
        assert data["content_origin"] == "https://content.desmos.lol"
        assert isinstance(data["browser_shortcuts"], list)

        shortcuts = {entry["id"]: entry for entry in data["browser_shortcuts"]}
        assert "tiktok" in shortcuts
        assert "youtube" in shortcuts
        assert shortcuts["tiktok"]["url"] == "https://www.tiktok.com/"
        assert shortcuts["youtube"]["url"] == "https://www.youtube.com/"

    def test_content_host_boundary_blocks_private_api_but_allows_config_and_game_content(self, monkeypatch):
        monkeypatch.setenv("CONTENT_ORIGIN", "https://content.desmos.lol")

        client = TestClient(app)
        private_api = client.get("/api/health", headers={"host": "content.desmos.lol"})
        assert private_api.status_code == 403
        assert "not available" in private_api.json().get("detail", "").lower()

        config_ok = client.get("/api/config", headers={"host": "content.desmos.lol"})
        assert config_ok.status_code == 200

        games_index = client.get("/api/games", headers={"host": "content.desmos.lol"})
        assert games_index.status_code == 403

        game_content = client.get("/api/games/2048.html/content", headers={"host": "content.desmos.lol"})
        assert game_content.status_code == 200
