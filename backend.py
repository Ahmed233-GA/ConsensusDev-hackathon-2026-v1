import os
import random
import time
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

# Optional: Anthropic client for LLM calls
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

app = FastAPI(title="ConsensusDev Demo Backend", version="0.1.0")

# In-memory storage for PR results
PR_STORE: List[Dict[str, Any]] = []

# ---------- Schemas ----------
class WebhookPayload(BaseModel):
    pr_number: int
    repo_name: str
    diff_text: str
    title: str = "Demo PR"

class Finding(BaseModel):
    severity: str
    tool: str
    file: str
    line: int
    title: str
    description: str

# ---------- Helper Functions ----------
def mock_scan() -> List[Finding]:
    """Return fake static analysis findings.
    For demo purposes we return two vulnerabilities and one code smell.
    """
    return [
        Finding(
            severity="HIGH",
            tool="Trivy",
            file="app.py",
            line=42,
            title="Hardcoded secret",
            description="Hardcoded API key found in source code.",
        ),
        Finding(
            severity="MEDIUM",
            tool="Checkov",
            file="db/config.py",
            line=12,
            title="SQL injection risk",
            description="User input directly concatenated into SQL query.",
        ),
        Finding(
            severity="LOW",
            tool="SonarQube",
            file="utils.py",
            line=5,
            title="Code smell",
            description="Method is too complex (cognitive complexity > 15).",
        ),
    ]

def call_llm(diff: str, findings: List[Finding]) -> Dict[str, Any]:
    """Send diff and findings to Anthropic LLM and parse structured JSON response.
    The system prompt instructs four agents that each return a verdict and reason.
    Returns a dict with keys: agents (dict), consensus (bool), consensus_reason (str).
    """
    if Anthropic is None:
        raise RuntimeError("Anthropic SDK not installed")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
    client = Anthropic(api_key=api_key)
    system_prompt = (
        "You are a multi-agent PR reviewer. Act as four specialized reviewers (Security, Technical Debt, Story Matching, Performance) in one pass. "
        "For each reviewer output a JSON object with fields 'verdict' (approve or request_changes) and 'reason' (one line). "
        "Also output a top-level 'consensus' field which is true if the majority verdict is approve, and a 'consensus_reason' explaining the overall decision. "
        "Use the provided static analysis findings as context for the Security reviewer. "
        "Return ONLY valid JSON with the following structure: {\"agents\": {\"security\": {\"verdict\": ..., \"reason\": ...}, \"tech_debt\": {...}, \"story\": {...}, \"performance\": {...}}, \"consensus\": true|false, \"consensus_reason\": \"...\"}."
    )
    findings_text = "\n".join(
        [
            f"- [{f.severity}] {f.title} ({f.tool}) in {f.file}:{f.line}: {f.description}" for f in findings
        ]
    )
    user_prompt = f"Diff:\n{diff}\n\nStatic Findings:\n{findings_text}\n"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        temperature=0.0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    content = response.content[0].text if isinstance(response.content, list) else response.content
    try:
        import json
        data = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nRaw content: {content}")
    return data

# ---------- Endpoints ----------
@app.post("/mock-scan")
def get_mock_scan():
    return [f.dict() for f in mock_scan()]

@app.post("/webhook")
def webhook(payload: WebhookPayload):
    review_time_ms = random.randint(2000, 5000)
    time.sleep(review_time_ms / 1000.0)
    findings = mock_scan()
    try:
        llm_result = call_llm(payload.diff_text, findings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    agents = llm_result.get("agents", {})
    for key in ["security", "tech_debt", "story", "performance"]:
        if key not in agents:
            agents[key] = {"verdict": "request_changes", "reason": "Missing agent output"}
    result = {
        "pr_number": payload.pr_number,
        "title": payload.title,
        "diff_text": payload.diff_text,
        "review_time_ms": review_time_ms,
        "findings": [f.dict() for f in findings],
        "agents": agents,
        "consensus": "approve" if llm_result.get("consensus") else "request_changes",
        "consensus_reason": llm_result.get("consensus_reason", ""),
    }
    PR_STORE.insert(0, result)
    return result

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-tests")
def run_tests(payload: dict):
    diff = payload.get("diff", "").strip()
    if not diff:
        raise HTTPException(status_code=400, detail="Diff cannot be empty")
    # Simulated test execution results
    return {
        "test_results": {"passed": True},
        "coverage_percentage": 85.0,
        "mutation_score": 92.0,
    }

@app.get("/metrics")
def metrics():
    total = len(PR_STORE)
    approved = sum(1 for p in PR_STORE if p["consensus"] == "approve")
    approval_rate = round((approved / total) * 100, 1) if total else 0
    avg_time_ms = round(sum(p["review_time_ms"] for p in PR_STORE) / total, 1) if total else 0
    vulns = sum(
        1
        for p in PR_STORE
        for f in p.get("findings", [])
        if f.get("severity", "").upper() in ["HIGH", "MEDIUM"]
    )
    return {
        "total_reviewed": total,
        "approval_rate": approval_rate,
        "avg_review_time_label": f"{avg_time_ms/1000:.1f}s",
        "vulnerabilities_caught": vulns,
    }

@app.get("/prs")
def list_prs():
    return {"prs": PR_STORE}

@app.get("/health")
def health_simple():
    return {"status": "ok"}
