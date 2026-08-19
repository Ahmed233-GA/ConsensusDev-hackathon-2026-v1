# Branch Summary — feature/shahd-qa

**Owner:** Shahd Mostafa
**Service:** Test & QA (`qa_runner/`)
**Port:** 8003
**Branch:** `feature/shahd-qa`

---

## What This Branch Adds

A FastAPI service that runs the project's automated test suite, measures real code coverage, and returns a heuristic mutation score — providing the AI Engine with actual QA evidence instead of guesses.

### Files added/changed
```
qa_runner/
├── __init__.py
├── main.py
└── requirements.txt
tests/
└── test_qa_runner.py
conftest.py
.gitignore   (updated)
```

---

## Endpoints

### `GET /health`
Basic health check.

**Response:**
```json
{ "status": "ok" }
```

### `POST /run-tests`
Runs the project's test suite and returns results, coverage, and a mutation score.

**Request:**
```json
{ "diff": "some code diff" }
```

**Response (200):**
```json
{
  "test_results": {
    "total": 3,
    "passed": 3,
    "failed": 0,
    "details": []
  },
  "coverage_percentage": 84.7,
  "mutation_score": 84.7
}
```

**Error responses:**
- `400` — empty/blank `diff` payload
- `500` — unexpected error during test execution

---

## ✅ Done

- [x] `GET /health` endpoint
- [x] `POST /run-tests` endpoint accepting `{ diff }`
- [x] **Real** pytest execution (not mocked) — runs the project's actual test suite via `coverage run -m pytest`
- [x] **Real** coverage measurement via `coverage.py`, parsed from `coverage.json`
- [x] Coverage field name **unified** to `coverage_percentage` only (resolves the `coverage_percentage` vs `coverage_pct` inconsistency noted in the team handoff guide)
- [x] Mutation score field (`mutation_score`) added to the response
- [x] Error handling: 400 for empty diff, 500 for unexpected failures
- [x] Unit tests (`tests/test_qa_runner.py`) covering health check, valid diff, and empty diff — all passing
- [x] `.gitignore` updated so `.coverage` and `coverage.json` (generated at runtime) are never committed

---

## ⚠️ Known Limitations (by design, hackathon scope)

1. **Mutation score is a heuristic approximation**, not a real `mutmut`/`cosmic-ray` run. It's currently derived from the pass rate and coverage percentage. A real mutation-testing pass would be the next step post-hackathon (noted in code comments).
2. **The `diff` payload is logged but not yet applied** to the codebase before running tests — the endpoint currently runs the project's existing test suite as-is. Applying the incoming diff to a temporary checkout before running tests is a planned follow-up, not yet implemented.
3. The service runs the **whole project's** test suite (excluding its own test file) rather than a scoped subset — acceptable for now since diff-based test selection isn't implemented yet.

---

## How to Run Locally

```bash
pip install -r qa_runner/requirements.txt
python -m uvicorn qa_runner.main:app --reload --port 8003
```

## How to Run Tests

```bash
pytest tests/test_qa_runner.py -v
```

---

## Integration Notes for Ahmed (Gateway)

- Call `POST http://localhost:8003/run-tests` with `{ "diff": "<diff content>" }`
- Expect `test_results`, `coverage_percentage`, and `mutation_score` in the response — pass all three into Medhat's `/analyze` payload as real QA evidence.
- Handle `400` (bad input) and `500` (execution failure) from this service gracefully in the Gateway's orchestration logic.

---

## Next Steps (Post-Hackathon / Future Work)

- Replace heuristic `mutation_score` with a real `mutmut` (or similar) integration.
- Actually apply the incoming `diff` to a temporary checkout before running tests, so results reflect the specific change under review rather than the whole existing suite.
- Expand `test_results.details` with per-test pass/fail breakdown instead of an empty list.

---

*This branch does not touch `main`, `gateway/`, or `scanners/`. Ready for review and PR by the integration owner.*