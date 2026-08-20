import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-PortalDocs")

app = FastAPI(
    title="ConsensusDev Portal & Documentation Service",
    description="Live Documentation, PR Changelogs, and DORA Telemetry (Port 8004)",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url=None,
)


class UpdateDocsRequest(BaseModel):
    repo: str
    pr_number: int
    status: str = "merged"
    author: str = "Developer"
    metrics: Optional[Dict[str, Any]] = None


class UpdateDocsResponse(BaseModel):
    docs_updated: bool = True
    dashboard_refreshed: bool = True
    changelog_entry: str


_docs_history: List[Dict[str, Any]] = []


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Portal & Documentation Service",
        "port": 8004,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "portal_docs",
        "port": 8004,
    }


@app.post("/update-docs", response_model=UpdateDocsResponse)
async def update_docs(request: UpdateDocsRequest):
    """
    Contract 4: Port 8004
    Updates live documentation and records PR changelog on merge.
    """
    logger.info(f"Updating documentation and changelog for PR #{request.pr_number} in {request.repo} by @{request.author}")
    entry = f"PR #{request.pr_number} merged by @{request.author}: Status {request.status}"
    _docs_history.append({
        "repo": request.repo,
        "pr_number": request.pr_number,
        "author": request.author,
        "metrics": request.metrics or {},
        "timestamp": entry,
    })
    return UpdateDocsResponse(
        docs_updated=True,
        dashboard_refreshed=True,
        changelog_entry=entry,
    )


@app.get("/docs")
async def get_docs():
    return {
        "title": "ConsensusDev Architectural Documentation",
        "history": _docs_history,
    }


@app.get("/metrics")
async def get_metrics():
    total = len(_docs_history)
    scores = [h.get("metrics", {}).get("consensus_score", 0) for h in _docs_history if "metrics" in h]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    return {
        "total_prs_documented": total,
        "average_consensus_score": avg_score,
        "history": _docs_history,
    }
