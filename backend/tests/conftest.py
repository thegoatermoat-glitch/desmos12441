import os
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values


@pytest.fixture(scope="session")
def base_url() -> str:
    # Shared API base URL from environment/frontend .env
    env_url = os.environ.get("REACT_APP_BACKEND_URL")
    if not env_url:
        frontend_env = dotenv_values(Path(__file__).resolve().parents[2] / "frontend" / ".env")
        env_url = frontend_env.get("REACT_APP_BACKEND_URL")
    if not env_url:
        pytest.skip("REACT_APP_BACKEND_URL is not configured")
    return env_url.rstrip("/")


@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
