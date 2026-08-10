"""
ConsensusDev — Multi-Agent AI PR Review Backend
FastAPI webhook server that simulates a GitHub PR event, routes code diffs
to 4 specialized AI agents (Security, Technical Debt, Story Matching,
Performance) via the Anthropic API, and stores results in memory for the
Streamlit dashboard to poll.

Run:
    uvicorn backend:app --reload --port 8000
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore[assignment]

app = FastAPI(title="ConsensusDev API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store of processed PR results
_pr_store: list[dict[str, Any]] = []

ANTHROPIC_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
You are ConsensusDev, a multi-agent code review system. You simulate 4 \
specialized AI reviewers debating a pull request diff in a single pass.

Return ONLY valid JSON (no markdown, no prose) with this exact shape:
{
  "security":        {"verdict": "approve"|"request_changes", "reason": "<one line>"},
  "tech_debt":       {"verdict": "approve"|"request_changes", "reason": "<one line>"},
  "story":           {"verdict": "approve"|"request_changes", "reason": "<one line>"},
  "performance":     {"verdict": "approve"|"request_changes", "reason": "<one line>"},
  "consensus":       "approve"|"request_changes",
  "consensus_reason":"<one line summarizing the majority vote>"
}

Rules:
- "security" flags secrets, injection (SQL/XSS), unsafe deserialization.
- "tech_debt" flags duplication, legacy patterns, missing tests, code smells.
- "story" checks if the diff matches the PR title / stated intent.
- "performance" flags N+1 queries, unbounded loops, missing caching/lazy load.
- consensus = "approve" only if 3 or more agents approve (majority).
- Each reason must be a single concise sentence.
"""


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class WebhookPayload(BaseModel):
    pr_number: int
    repo_name: str
    diff_text: str = Field(..., description="Unified git diff of the PR")
    title: str = ""
    branch: str = ""
    author: str = ""


class ScanFinding(BaseModel):
    tool: str
    severity: str  # critical | high | medium | low
    title: str
    file: str
    line: int
    description: str


# ---------------------------------------------------------------------------
# Mock static-analysis endpoint (Member 3 — Soliman / SonarQube step)
# ---------------------------------------------------------------------------

def _mock_scan_findings(diff_text: str) -> list[dict[str, Any]]:
    """Return fake SAST/IaC findings based on simple pattern matching."""
    findings: list[dict[str, Any]] = []

    if any(k in diff_text.lower() for k in ("password", "secret", "api_key", "token", "sk-")):
        findings.append({
            "id": str(uuid.uuid4())[:8],
            "tool": "Trivy + Gitleaks",
            "severity": "critical",
            "title": "Hardcoded secret detected",
            "file": "src/api/users.py",
            "line": 16,
            "description": "A plaintext credential is committed to source. "
                           "Rotate the secret and move it to a vault.",
        })

    if "f\"SELECT" in diff_text or "execute(f\"" in diff_text:
        findings.append({
            "id": str(uuid.uuid4())[:8],
            "tool": "SonarQube",
            "severity": "critical",
            "title": "SQL injection via string interpolation",
            "file": "src/api/users.py",
            "line": 21,
            "description": "User input is concatenated into a SQL query. "
                           "Use parameterized queries.",
        })

    if "require(" in diff_text:
        findings.append({
            "id": str(uuid.uuid4())[:8],
            "tool": "Semgrep",
            "severity": "medium",
            "title": "Legacy synchronous require() in ES module",
            "file": "src/components/ProductGrid.tsx",
            "line": 7,
            "description": "CommonJS require() blocks tree-shaking.",
        })

    # Always add one low-severity code smell
    findings.append({
        "id": str(uuid.uuid4())[:8],
        "tool": "SonarQube",
        "severity": "low",
        "title": "Code smell: long parameter list",
        "file": "src/api/users.py",
        "line": 12,
        "description": "Consider grouping related parameters into a dataclass.",
    })

    return findings


@app.get("/mock-scan")
def mock_scan(diff_text: str = "") -> dict[str, Any]:
    """Return fake static-analysis findings for a given diff."""
    return {"findings": _mock_scan_findings(diff_text)}


# ---------------------------------------------------------------------------
# LLM call (Member 1 — Mohammed Medhat / AI Brain)
# ---------------------------------------------------------------------------

def run_multi_agent_review(
    diff_text: str,
    findings: list[dict[str, Any]],
    pr_title: str = "",
) -> dict[str, Any]:
    """Send the diff + scan findings to Claude with the 4-agent system prompt."""
    findings_str = json.dumps(findings, indent=2) if findings else "[]"

    user_msg = (
        f"PR title: {pr_title or '(not provided)'}\n\n"
        f"Static analysis findings (from SAST/IaC tools):\n{findings_str}\n\n"
        f"Code diff:\n```diff\n{diff_text}\n```\n\n"
        "Return the JSON verdict from all 4 agents and the consensus."
    )

    # --- Real Anthropic call -------------------------------------------------
    if anthropic and (key := _get_api_key()):
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = resp.content[0].text if resp.content else ""
        return _parse_llm_json(text)

    # --- Offline fallback (no API key) --------------------------------------
    return _offline_review(diff_text, findings)


def _get_api_key() -> str | None:
    import os
    return os.environ.get("ANTHROPIC_API_KEY")


def _parse_llm_json(text: str) -> dict[str, Any]:
    """Best-effort parse of the LLM JSON response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```json", 1)[-1].split("```", 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "security": {"verdict": "approve", "reason": "parse error"},
            "tech_debt": {"verdict": "approve", "reason": "parse error"},
            "story": {"verdict": "approve", "reason": "parse error"},
            "performance": {"verdict": "approve", "reason": "parse error"},
            "consensus": "approve",
            "consensus_reason": "LLM response could not be parsed; defaulting to approve.",
        }


def _offline_review(diff_text: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic fallback when no Anthropic API key is set."""
    has_critical = any(f["severity"] in ("critical", "high") for f in findings)
    has_medium = any(f["severity"] == "medium" for f in findings)

    sec = "request_changes" if has_critical else "approve"
    debt = "request_changes" if has_medium else "approve"

    agents = {
        "security": {
            "verdict": sec,
            "reason": "Critical finding: hardcoded secret and SQL injection." if has_critical
                      else "No credentials or injection sinks detected.",
        },
        "tech_debt": {
            "verdict": debt,
            "reason": "Legacy require() pattern adds maintainability debt." if has_medium
                      else "Clean module boundaries, no new debt.",
        },
        "story": {
            "verdict": "approve",
            "reason": "Implementation matches the PR title and branch intent.",
        },
        "performance": {
            "verdict": "approve",
            "reason": "No performance regressions detected.",
        },
    }
    approvals = sum(1 for v in agents.values() if v["verdict"] == "approve")
    consensus = "approve" if approvals >= 3 else "request_changes"
    return {
        **agents,
        "consensus": consensus,
        "consensus_reason": f"{approvals}/4 agents approved.",
    }


# ---------------------------------------------------------------------------
# Webhook endpoint (Member 2 — Ahmed Atia / Git Automation)
# ---------------------------------------------------------------------------

@app.post("/webhook")
def webhook(payload: WebhookPayload) -> dict[str, Any]:
    """Simulate receiving a GitHub PR webhook and running the review pipeline."""
    start = time.time()

    # 1. Run mock static scan (Member 3 step)
    findings = _mock_scan_findings(payload.diff_text)

    # 2. Send diff + findings to multi-agent LLM (Member 1 step)
    review = run_multi_agent_review(
        diff_text=payload.diff_text,
        findings=findings,
        pr_title=payload.title,
    )

    # 3. Simulate 2-5s review latency
    elapsed = time.time() - start
    if elapsed < 2.0:
        time.sleep(2.0 + (uuid.uuid4().int % 3000) / 1000.0)

    review_time_ms = int((time.time() - start) * 1000)

    result = {
        "id": str(uuid.uuid4())[:8],
        "pr_number": payload.pr_number,
        "repo_name": payload.repo_name,
        "title": payload.title,
        "branch": payload.branch,
        "author": payload.author,
        "diff_text": payload.diff_text,
        "findings": findings,
        "agents": {
            k: v for k, v in review.items()
            if k in ("security", "tech_debt", "story", "performance")
        },
        "consensus": review.get("consensus", "approve"),
        "consensus_reason": review.get("consensus_reason", ""),
        "review_time_ms": review_time_ms,
        "submitted_at": int(time.time()),
        "status": "completed",
    }

    _pr_store.insert(0, result)
    return result


# ---------------------------------------------------------------------------
# Dashboard data endpoints (Member 5 — Nourhan / Streamlit)
# ---------------------------------------------------------------------------

@app.get("/prs")
def list_prs() -> dict[str, Any]:
    return {"prs": _pr_store}


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    total = len(_pr_store) or 1
    approved = sum(1 for p in _pr_store if p["consensus"] == "approve")
    changes = total - approved if _pr_store else 0
    avg_ms = sum(p["review_time_ms"] for p in _pr_store) / total if _pr_store else 0
    vulns = sum(
        1 for p in _pr_store for f in p["findings"]
        if f["severity"] in ("critical", "high")
    )
    return {
        "total_reviewed": len(_pr_store),
        "approved": approved,
        "changes_requested": changes,
        "approval_rate": round(approved / total * 100) if _pr_store else 0,
        "avg_review_time_ms": int(avg_ms),
        "avg_review_time_label": f"{avg_ms / 1000:.1f}s",
        "vulnerabilities_caught": vulns,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
