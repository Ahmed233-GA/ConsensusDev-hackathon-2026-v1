import hashlib
import hmac
import json
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

        res_api_health = await client.get("/api/health")
        assert res_api_health.status_code == 200
        assert "services" in res_api_health.json()


@pytest.mark.asyncio
async def test_gateway_webhook_ping_event(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "test_secret_123")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"zen": "Keep it logically awesome.", "hook_id": 12345}
        raw_body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(b"test_secret_123", raw_body, hashlib.sha256).hexdigest()

        headers = {
            "x-github-event": "ping",
            "x-hub-signature-256": sig,
        }
        res = await client.post("/webhook/github", content=raw_body, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "connected"


@pytest.mark.asyncio
async def test_gateway_webhook_pull_request_event(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "test_secret_123")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "action": "opened",
            "number": 142,
            "pull_request": {
                "number": 142,
                "title": "Add Calculator feature",
                "user": {"login": "AhmedAtia"},
                "head": {"ref": "feature/calc", "sha": "1234567890abcdef"},
                "base": {
                    "ref": "main",
                    "repo": {
                        "full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1",
                        "owner": {"login": "Ahmed233-GA"},
                        "name": "ConsensusDev-hackathon-2026-v1",
                    },
                },
            },
        }
        raw_body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(b"test_secret_123", raw_body, hashlib.sha256).hexdigest()

        headers = {
            "x-github-event": "pull_request",
            "x-hub-signature-256": sig,
            "x-consensusdev-sync": "true",
            "x-github-delivery": "del-sync-142",
        }
        res = await client.post("/webhook/github", content=raw_body, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["processed_sync", "accepted"]
        assert "review" in data


@pytest.mark.asyncio
async def test_gateway_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. PR list
        res_prs = await client.get("/api/pull-requests")
        assert res_prs.status_code == 200
        assert "prs" in res_prs.json()

        # 2. Logs
        res_logs = await client.get("/api/logs")
        assert res_logs.status_code == 200
        assert "logs" in res_logs.json()

        # 3. Agents
        res_agents = await client.get("/api/agents")
        assert res_agents.status_code == 200
        assert len(res_agents.json()["agents"]) == 4
