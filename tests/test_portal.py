import pytest
from httpx import ASGITransport, AsyncClient
from portal.main import app


@pytest.mark.asyncio
async def test_portal_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        assert res.json()["port"] == 8004


@pytest.mark.asyncio
async def test_portal_update_docs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "repo": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1",
            "pr_number": 142,
            "status": "merged",
            "author": "AhmedSoliman",
            "metrics": {"consensus_score": 92, "review_time_seconds": 1.45},
        }
        res = await client.post("/update-docs", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["docs_updated"] is True
        assert "PR #142" in data["changelog_entry"]
