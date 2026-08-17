import pytest
from httpx import ASGITransport, AsyncClient
from ai_engine.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_analyze_pr_bad_pr_flow():
    """
    Step 1 / Contract 3 test: Bad PR with SQL injection and failed tests
    Expects consensus: False
    """
    payload = {
        "diff": "diff --git a/app/db.py b/app/db.py\n+ query = f'SELECT * FROM users WHERE id = {user_input}'",
        "security": {
            "status": "FAIL",
            "vulnerabilities_count": 1,
            "critical_issues": ["SQL Injection detected in app/db.py (CWE-89)"],
        },
        "tests": {
            "status": "FAIL",
            "tests_passed": 0,
            "tests_failed": 2,
            "coverage_percentage": 0.0,
        },
        "pr_number": 141,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analyze-pr", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["consensus"] is False
        assert "security" in data["agents_feedback"]
        assert "tech_debt" in data["agents_feedback"]
        assert "story_match" in data["agents_feedback"]
        assert "performance" in data["agents_feedback"]
        assert "failed consensus review" in data["summary"] or "blocked" in data["summary"].lower()


@pytest.mark.asyncio
async def test_analyze_pr_good_pr_flow():
    """
    Step 6 / Contract 3 test: Clean PR with parameterized queries and passing tests
    Expects consensus: True
    """
    payload = {
        "diff": "diff --git a/app/calc.py b/app/calc.py\n+ def add(a: int, b: int) -> int: return a + b",
        "security": {
            "status": "PASS",
            "vulnerabilities_count": 0,
            "critical_issues": [],
        },
        "tests": {
            "status": "PASS",
            "tests_passed": 12,
            "tests_failed": 0,
            "coverage_percentage": 95.0,
        },
        "pr_number": 142,
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/analyze-pr", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["consensus"] is True
        assert data["score"] >= 80
        assert "Approved for auto-merge" in data["summary"]
