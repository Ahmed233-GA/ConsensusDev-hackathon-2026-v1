# qa_runner/main.py
"""QA Runner FastAPI service.
Provides health check and a mock test execution endpoint.
The response includes a consistent `coverage_percentage` field.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

@app.get("/health")
async def health() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


class RunTestsRequest(BaseModel):
    diff: str

def execute_tests(diff: str) -> Dict[str, Any]:
    """Execute the project's pytest suite (excluding this endpoint's own test) and collect results.
    The `diff` argument is currently unused – it is logged for future implementation.
    """
    import sys, subprocess, os, re, json
    if not diff.strip():
        raise ValueError("Diff payload is empty")
    if diff.strip():
        print(f"[execute_tests] Received diff (ignored in hackathon scope): {diff[:200]}")
    # Run pytest under coverage to gather test results and coverage in a single run
    cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        "-m",
        "pytest",
        "-q",
        "-k",
        "not test_qa_runner",
    ]
    result = subprocess.run(cmd, cwd=os.getcwd(), capture_output=True, text=True)
    stdout = result.stdout.strip()
    # Parse pass/fail counts from pytest output, e.g., "3 passed, 0 failed"
    passed = failed = 0
    for part in stdout.split(","):
        m = re.search(r"(\d+)\s+passed", part)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", part)
        if m:
            failed = int(m.group(1))
    total = passed + failed
    details: list[dict[str, Any]] = []
    # Generate coverage report in JSON format
    coverage_percent = 0.0
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", "coverage.json"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
        )
        with open(os.path.join(os.getcwd(), "coverage.json"), "r", encoding="utf-8") as f:
            cov_data = json.load(f)
        coverage_percent = round(
            cov_data.get("totals", {}).get("percent_covered", 0.0), 2
        )
    except Exception:
        coverage_percent = 0.0
    # Heuristic mutation score (placeholder)
    mutation_score = 0.0
    if total:
        mutation_score = round((passed / total) * coverage_percent, 2)
    return {
        "test_results": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "details": details,
        },
        "coverage_percentage": coverage_percent,
        "mutation_score": mutation_score,
    }
# NOTE: execute_tests runs real pytest under coverage and provides a heuristic mutation_score placeholder. The diff is logged but not applied.

@app.post("/run-tests")
async def run_tests(request: RunTestsRequest) -> Dict[str, Any]:
    """Run tests for the given diff and return results with coverage and mutation score.
    Returns a JSON response containing `test_results`, `coverage_percentage`, and `mutation_score`.
    """
    try:
        result = execute_tests(request.diff)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=500, detail="Error during test execution")
