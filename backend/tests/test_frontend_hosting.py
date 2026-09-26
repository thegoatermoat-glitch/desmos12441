import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend_host import mount_frontend


# Production SPA hosting coverage: deep links, static assets, MIME headers, API/file security boundaries
def make_client() -> tuple[TestClient, Path]:
    build_dir = Path(__file__).resolve().parents[2] / "frontend" / "build"
    os.environ["SERVE_FRONTEND"] = "true"
    os.environ["FRONTEND_BUILD_DIR"] = str(build_dir)

    app = FastAPI()

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    mount_frontend(app)
    return TestClient(app), build_dir


class TestFrontendHosting:
    def test_spa_deep_links_return_index(self):
        client, _ = make_client()
        for route in ["/", "/library", "/web", "/notes"]:
            response = client.get(route)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert "Desmos | Testing" in response.text

    def test_static_assets_and_mime_types(self):
        client, build_dir = make_client()

        index = client.get("/index.html")
        assert index.status_code == 200
        assert "text/html" in index.headers.get("content-type", "")

        wasm = client.get("/scramjet/scramjet.wasm.wasm")
        assert wasm.status_code == 200
        assert "application/wasm" in wasm.headers.get("content-type", "")

        module = client.get("/epoxy/index.mjs")
        assert module.status_code == 200
        assert "application/javascript" in module.headers.get("content-type", "")

        first_font = next((build_dir / "static" / "media").glob("*.woff2"), None)
        assert first_font is not None
        font = client.get(f"/static/media/{first_font.name}")
        assert font.status_code == 200
        assert "font" in font.headers.get("content-type", "") or "application/octet-stream" in font.headers.get("content-type", "")

    def test_api_and_path_boundaries(self):
        client, _ = make_client()

        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        api_unknown = client.get("/api/does-not-exist")
        assert api_unknown.status_code == 404
        assert "text/html" not in api_unknown.headers.get("content-type", "")

        path_traversal = client.get("/..%2F..%2Fetc%2Fpasswd.js")
        assert path_traversal.status_code == 404
        assert "not found" in path_traversal.json().get("detail", "").lower()
