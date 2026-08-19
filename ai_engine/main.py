import os
os.environ["LITELLM_LOG"] = "ERROR"

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Ensure both package import and direct execution work
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ai_engine.agents.security_agent import review_security
    from ai_engine.agents.performance_agent import review_performance
    from ai_engine.agents.story_match_agent import review_story_match
    from ai_engine.agents.tech_debt_agent import review_tech_debt
except ImportError:
    from agents.security_agent import review_security
    from agents.performance_agent import review_performance
    from agents.story_match_agent import review_story_match
    from agents.tech_debt_agent import review_tech_debt

app = FastAPI(title="ConsensusDev AI Engine")


# ---- Request/response contract with Ahmed ----

class ReviewRequest(BaseModel):
    diff: str
    ticket_description: str = ""   # optional, defaults to empty if not provided


class AgentResult(BaseModel):
    agent: str
    verdict: str
    issues: List[str]


class ReviewResponse(BaseModel):
    overall_verdict: str
    agents: List[AgentResult]


# ---- Core logic (same pattern as run_all.py) ----

def run_all_agents(diff: str, ticket: str) -> List[AgentResult]:
    jobs = {
        "security": lambda: review_security(diff),
        "performance": lambda: review_performance(diff),
        "story_match": lambda: review_story_match(diff, ticket),
        "tech_debt": lambda: review_tech_debt(diff),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        future_to_name = {executor.submit(fn): name for name, fn in jobs.items()}
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = {"verdict": "error", "issues": [f"Runner failed: {e}"]}

    return [
        AgentResult(agent=name, verdict=r.get("verdict", "unknown"), issues=r.get("issues", []))
        for name, r in results.items()
    ]


# ---- The endpoint Ahmed will call ----

@app.post("/review", response_model=ReviewResponse)
def review_pr(request: ReviewRequest):
    agent_results = run_all_agents(request.diff, request.ticket_description)

    overall = "pass" if all(a.verdict == "pass" for a in agent_results) else "fail"

    return ReviewResponse(
        overall_verdict=overall,
        agents=agent_results,
    )


# ---- Simple health check, useful for Ahmed to confirm you're online ----

@app.get("/health")
def health():
    return {"status": "ok"}