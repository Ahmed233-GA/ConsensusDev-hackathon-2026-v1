import pytest
from httpx import ASGITransport, AsyncClient

from gateway.main import app


@pytest.mark.asyncio
async def test_gateway_root_and_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert res.json()["service"] == "ConsensusDev Gateway"

        res_health = await client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_gateway_webhook_ping_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"x-github-event": "ping"}
        payload = {"zen": "Keep it logically awesome.", "hook_id": 12345}
        res = await client.post("/webhook/github", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "connected"


@pytest.mark.asyncio
async def test_gateway_webhook_pull_request_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"x-github-event": "pull_request"}
        payload = {
            "action": "opened",
            "number": 142,
            "pull_request": {
                "number": 142,
                "title": "Add Calculator feature",
                "user": {"login": "AhmedAtia"},
                "base": {
                    "repo": {
                        "full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1",
                        "owner": {"login": "Ahmed233-GA"},
                        "name": "ConsensusDev-hackathon-2026-v1",
                    }
                },
            },
        }
        res = await client.post("/webhook/github", json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "processed"
        assert "orchestration_result" in data
