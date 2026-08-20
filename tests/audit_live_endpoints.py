import json
import urllib.request
import time


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Verifier"},
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Verifier"})
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def main():
    print("=== 1. GATEWAY REST API (:8000) ===")
    s, r = get("http://127.0.0.1:8000/api/agents")
    print(f"GET /api/agents -> {s}, {len(r['agents'])} agents")

    s, r = get("http://127.0.0.1:8000/api/logs")
    print(f"GET /api/logs -> {s}, {len(r['logs'])} logs")

    s, r = get("http://127.0.0.1:8000/api/pull-requests")
    print(f"GET /api/pull-requests -> {s}, {len(r['prs'])} prs")

    print("\n=== 2. SECURITY SCANNER (:8002) ===")
    s, r = post(
        "http://127.0.0.1:8002/scan",
        {"diff": "diff --git a/app.py b/app.py\n+password = 'secret123'"},
    )
    print(
        f"POST /scan (Secret) -> Status: {r.get('status')}, Vulns: {r.get('vulnerabilities_count')}, Findings: {len(r.get('findings', []))}"
    )

    print("\n=== 3. QA RUNNER (:8003) ===")
    s, r = post(
        "http://127.0.0.1:8003/run-tests",
        {"diff": "diff --git a/calc.py b/calc.py\n+def add(a, b): return a + b", "pr_number": 99},
    )
    print(
        f"POST /run-tests -> Status: {r.get('status')}, Passed: {r.get('tests_passed')}, Cov: {r.get('coverage_percentage')}%, Mut: {r.get('mutation_score')}%"
    )

    print("\n=== 4. AI ENGINE (:8001) ===")
    s, r = post(
        "http://127.0.0.1:8001/analyze-pr",
        {
            "diff": "diff --git a/calc.py b/calc.py\n+def add(a, b): return a + b",
            "security": {"status": "PASS", "available": True, "vulnerabilities_count": 0, "critical_issues": []},
            "tests": {"status": "PASS", "available": True, "tests_passed": 5, "tests_failed": 0, "coverage_percentage": 90.0, "mutation_score": 85.0},
            "pr_number": 142,
        },
    )
    print(f"POST /analyze-pr -> {s}, Consensus: {r.get('consensus')}, Score: {r.get('score')}/100")

    print("\n=== 5. PORTAL DOCS (:8004) ===")
    s, r = post(
        "http://127.0.0.1:8004/update-docs",
        {
            "repo": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1",
            "pr_number": 142,
            "status": "merged",
            "author": "Ahmed",
            "metrics": {"consensus_score": 90, "review_time_seconds": 1.5},
        },
    )
    print(f"POST /update-docs -> {s}, Updated: {r.get('docs_updated')}")

    s, r = get("http://127.0.0.1:8004/docs")
    print(f"GET /docs -> {s}, {r.get('title')}")


if __name__ == "__main__":
    main()
