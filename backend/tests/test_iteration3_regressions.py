import json
from pathlib import Path


# Iteration-3 regressions: games covers metadata/files, reader-mode config, and CSP/sandbox headers.
class TestIteration3Regressions:
    def test_games_count_and_cover_count_exact(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/games")
        assert response.status_code == 200
        games = response.json()
        assert len(games) == 300

        with_cover = [g for g in games if g.get("cover")]
        assert len(with_cover) == 158

    def test_cover_metadata_matches_local_files(self):
        root = Path(__file__).resolve().parents[2]
        covers_map = json.loads((root / "backend" / "data" / "game-covers.json").read_text())
        cover_dir = root / "frontend" / "public" / "covers"

        assert len(covers_map) == 158
        assert cover_dir.is_dir()

        png_files = list(cover_dir.glob("*.png"))
        assert len(png_files) == 158

        missing = []
        for game_id, payload in covers_map.items():
            rel = payload.get("cover", "")
            assert rel.startswith("/covers/")
            local = root / "frontend" / "public" / rel.lstrip("/")
            if not local.is_file():
                missing.append((game_id, rel))
        assert missing == []

    def test_reader_mode_config_when_content_origin_blank(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/config")
        assert response.status_code == 200
        data = response.json()
        assert data["content_origin"] == ""
        assert isinstance(data["wisp_endpoints"], list)
        assert len(data["wisp_endpoints"]) >= 2

    def test_game_content_csp_excludes_allow_same_origin_on_app_origin(self, api_client, base_url):
        response = api_client.get(f"{base_url}/api/games/2048.html/content")
        assert response.status_code == 200
        csp = response.headers.get("content-security-policy", "")
        assert "sandbox" in csp
        assert "allow-scripts" in csp
        assert "allow-same-origin" not in csp

    def test_browse_service_not_serving_react_spa_bundle(self, api_client, base_url):
        # Preview should not return React app shell for content-service route.
        response = api_client.get(f"{base_url}/browse/service/health")
        assert response.status_code in (404, 503)
        text = response.text.lower()
        assert "static/js/bundle.js" not in text