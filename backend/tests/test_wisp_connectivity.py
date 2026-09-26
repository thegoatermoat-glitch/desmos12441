import asyncio
from pathlib import Path

import pytest
from dotenv import dotenv_values
import websockets


# Live Wisp connectivity coverage: both configured endpoints should handshake without subprotocol and emit INFO/CONTINUE packet
ENV = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
WISP_ENDPOINTS = [e.strip() for e in ENV.get("WISP_ENDPOINTS", "").split(",") if e.strip()]


async def _probe(endpoint: str):
    async with websockets.connect(endpoint, open_timeout=10, ping_interval=None) as ws:
        packet = await asyncio.wait_for(ws.recv(), timeout=10)
        assert isinstance(packet, (bytes, bytearray))
        assert len(packet) >= 5
        assert packet[0] in (3, 5)
        assert packet[1:5] == b"\x00\x00\x00\x00"


@pytest.mark.anyio
@pytest.mark.parametrize("endpoint", WISP_ENDPOINTS)
async def test_wisp_endpoints_handshake(endpoint):
    if not WISP_ENDPOINTS:
        pytest.skip("No WISP_ENDPOINTS configured")
    await _probe(endpoint)
