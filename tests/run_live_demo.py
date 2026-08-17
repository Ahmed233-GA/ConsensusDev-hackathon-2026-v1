import asyncio
import json
import httpx
from ai_engine.main import app


async def run_live_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8001") as client:
        print("=" * 70)
        print("[TEST 1] Health Check Endpoint (GET /health)")
        print("=" * 70)
        res_health = await client.get("/health")
        print(f"Status Code: {res_health.status_code}")
        print(f"Response: {res_health.json()}\n")

        print("=" * 70)
        print("[TEST 2] Bad PR Flow (Step 1 Demo: SQL Injection + Failing QA)")
        print("=" * 70)
        bad_payload = {
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
        res_bad = await client.post("/analyze-pr", json=bad_payload)
        bad_data = res_bad.json()
        print(json.dumps(bad_data, indent=2))
        print(f"\n>>> Consensus Decision: {bad_data['consensus']} (AUTO-MERGE BLOCKED [X])\n")

        print("=" * 70)
        print("[TEST 3] Good PR Flow (Step 6 Demo: Clean Code + 95% QA Coverage)")
        print("=" * 70)
        good_payload = {
            "diff": "diff --git a/app/calc.py b/app/calc.py\n+ def add(a: int, b: int) -> int:\n+     return a + b",
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
        res_good = await client.post("/analyze-pr", json=good_payload)
        good_data = res_good.json()
        print(json.dumps(good_data, indent=2))
        print(f"\n>>> Consensus Decision: {good_data['consensus']} (APPROVED FOR AUTO-MERGE [OK])")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_live_tests())
