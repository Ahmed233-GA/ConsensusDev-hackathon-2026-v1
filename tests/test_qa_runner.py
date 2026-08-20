import pytest
from httpx import ASGITransport, AsyncClient
from qa_runner.main import app


@pytest.mark.asyncio
async def test_qa_runner_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        assert res.json()["port"] == 8003


@pytest.mark.asyncio
async def test_qa_runner_passes_clean_code():
    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,3 +1,3 @@
+def add(a: int, b: int) -> int:
+    return a + b
"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/run-tests", json={"diff": clean_diff, "pr_number": 101})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "PASS"
        assert data["available"] is True
        assert data["tests_passed"] >= 1
        assert data["tests_failed"] == 0
        assert data["coverage_percentage"] is not None
        assert data["coverage_percentage"] >= 80.0
        assert data["mutation_score"] is not None


@pytest.mark.asyncio
async def test_qa_runner_fails_on_assertion_error():
    failing_diff = """diff --git a/tests/test_sample.py b/tests/test_sample.py
+++ b/tests/test_sample.py
@@ -1,3 +1,3 @@
+def test_broken_feature():
+    assert False, "Regression detected in PR"
"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/run-tests", json={"diff": failing_diff, "pr_number": 102})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "FAIL"
        assert data["tests_failed"] >= 1
