import pytest
from httpx import ASGITransport, AsyncClient

from scanners.main import app


@pytest.mark.asyncio
async def test_scanners_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_scanners_detect_sql_injection_and_secrets():
    """
    Contract 1: Test Soliman Security Scanner with vulnerable diff.
    """
    bad_diff = """diff --git a/app/db.py b/app/db.py
+++ b/app/db.py
@@ -1,3 +1,3 @@
+query = f"SELECT * FROM users WHERE id = {user_input}"
+api_key = "sk-1234567890abcdef1234567890abcdef"
"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/scan", json={"diff": bad_diff})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "FAIL"
        assert data["vulnerabilities_count"] >= 1
        assert len(data["critical_issues"]) >= 1
        assert "checkov" in data["scanners"]
        assert "trivy" in data["scanners"]


@pytest.mark.asyncio
async def test_scanners_pass_clean_diff():
    """
    Contract 1: Test Soliman Security Scanner with clean diff.
    """
    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int:
+    return a + b
"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/scan", json={"diff": clean_diff})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "PASS"
        assert data["vulnerabilities_count"] == 0
