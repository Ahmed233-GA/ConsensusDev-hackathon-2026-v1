import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from gateway.github_client import GitHubClient
from gateway.models.review import PullRequestReview
from gateway.orchestrator import PipelineOrchestrator
from gateway.store import store
from gateway.database import init_db, get_db, get_dashboard_stats_from_db, SessionLocal
from gateway.models.db import User, ApprovalEventRecord, ReviewRecord
from gateway.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from gateway.seed_admin import seed_admin_user

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-Gateway")


def _load_env():
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


_load_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database schema and seed default admin user
    try:
        init_db()
        seed_admin_user()
        logger.info("Database and Admin user initialized on startup.")
    except Exception as e:
        logger.error(f"Startup initialization error: {e}")
    yield
    # Shutdown: Clean up if needed
    logger.info("Gateway shutting down.")


app = FastAPI(
    title="ConsensusDev Gateway",
    description="Central Orchestration Gateway, Webhook Ingestion, Auth & REST API (Port 8000)",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite Frontend (:3000) and Portal (:8004)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

github_client = GitHubClient()
orchestrator = PipelineOrchestrator(github_client=github_client)


class LoginRequest(BaseModel):
    operator_id: Optional[str] = Field(None, description="Username or email of the operator")
    username: Optional[str] = Field(None, description="Username alias")
    email: Optional[str] = Field(None, description="Email alias")
    access_key: Optional[str] = Field(None, description="Password / Access Key")
    password: Optional[str] = Field(None, description="Password alias")


class ManualTriggerRequest(BaseModel):
    diff: str = Field(..., description="Git unified diff text")
    pr_number: int = Field(101, description="PR Number")
    title: str = Field("Manual PR Review", description="PR Title")
    author: str = Field("Developer", description="PR Author username")
    branch: str = Field("feature/manual-check", description="Source branch")


class ApprovalRequest(BaseModel):
    actor: str = Field("Admin", description="Operator name or ID")
    reason: Optional[str] = Field("Manual approval from dashboard", description="Justification")


# ==========================================
# Authentication Endpoints
# ==========================================

@app.post("/auth/login")
@app.post("/api/auth/login")
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate operator credentials and issue a signed JWT session token.
    """
    identifier = request.operator_id or request.username or request.email
    password = request.access_key or request.password

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both operator_id (email/username) and access_key (password) are required",
        )

    user = authenticate_user(identifier, password, db)
    if not user:
        store.add_log(
            service="Gateway",
            level="WARN",
            message=f"Failed login attempt for operator: '{identifier}'",
            details={"identifier": identifier, "event": "AUTH_FAILED"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Operator ID or Access Key",
        )

    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.role, "email": user.email})

    # Set secure HTTP-only session cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )

    store.add_log(
        service="Gateway",
        level="INFO",
        message=f"Operator '{user.username}' successfully authenticated",
        details={"user_id": user.id, "username": user.username, "role": user.role, "event": "AUTH_SUCCESS"},
    )

    return {
        "status": "authenticated",
        "token": token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


@app.post("/auth/logout")
@app.post("/api/auth/logout")
async def logout(response: Response):
    """
    Log out operator and clear session cookie.
    """
    response.delete_cookie("access_token")
    return {"status": "logged_out", "message": "Operator session terminated"}


@app.get("/auth/me")
@app.get("/api/auth/me")
async def get_current_operator(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the currently authenticated operator.
    """
    return {
        "status": "authenticated",
        "user": current_user.to_dict(),
    }


# ==========================================
# Core Gateway Endpoints
# ==========================================

@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Gateway",
        "port": 8000,
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "auth_login": "/auth/login",
            "auth_me": "/auth/me",
            "webhook": "/webhook/github",
            "pull_requests": "/api/pull-requests",
            "stats": "/api/stats",
            "health": "/api/health",
            "logs": "/api/logs",
            "agents": "/api/agents",
        },
    }


@app.get("/health")
async def basic_health():
    return {
        "status": "healthy",
        "service": "gateway",
        "port": 8000,
    }


@app.get("/api/health")
async def aggregate_health():
    """
    Aggregate health check probing all 5 backend microservices:
    - Gateway (:8000)
    - AI Engine (:8001)
    - Security Scanner (:8002)
    - QA Runner (:8003)
    - Portal & Docs (:8004)
    """
    services = {
        "gateway": {"port": 8000, "url": "http://localhost:8000/health", "status": "online", "latencyMs": 1},
        "aiEngine": {"port": 8001, "url": "http://localhost:8001/health", "status": "offline", "latencyMs": 0},
        "scanners": {"port": 8002, "url": "http://localhost:8002/health", "status": "offline", "latencyMs": 0},
        "qaRunner": {"port": 8003, "url": "http://localhost:8003/health", "status": "offline", "latencyMs": 0},
        "portal": {"port": 8004, "url": "http://localhost:8004/health", "status": "offline", "latencyMs": 0},
    }

    async def probe_service(key: str, s_info: dict):
        if key == "gateway":
            return
        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(s_info["url"])
                latency = int((time.time() - t0) * 1000)
                if resp.status_code == 200:
                    s_info["status"] = "online"
                    s_info["latencyMs"] = latency
                else:
                    s_info["status"] = "degraded"
                    s_info["latencyMs"] = latency
        except Exception:
            s_info["status"] = "offline"
            s_info["latencyMs"] = 0

    probes = [probe_service(k, v) for k, v in services.items()]
    await asyncio.gather(*probes)

    all_online = all(v["status"] == "online" for v in services.values())
    return {
        "status": "healthy" if all_online else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": services,
    }


@app.get("/api/stats")
async def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Returns real aggregated statistics queried from the SQLite database.
    """
    stats = get_dashboard_stats_from_db(db)
    return stats


@app.post("/webhook/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default="pull_request"),
    x_hub_signature_256: str = Header(default=None),
    x_github_delivery: str = Header(default=None),
):
    """
    GitHub Webhook receiver.
    Validates HMAC signature, prevents duplicate deliveries with idempotency keys,
    and runs the 5-service autonomous review pipeline asynchronously.
    """
    payload_body = await request.body()
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    allow_unsigned_dev = os.getenv("WEBHOOK_ALLOW_UNSIGNED_DEV", "false").lower() in ["true", "1", "yes"]

    # 1. HMAC-SHA256 Signature Verification
    if not github_client.verify_webhook_signature(
        payload_body, x_hub_signature_256, webhook_secret, allow_unsigned_dev=allow_unsigned_dev
    ):
        logger.warning("Invalid or missing GitHub webhook HMAC signature received.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC-SHA256 signature",
        )

    payload = await request.json()

    # 2. Handle GitHub ping test event
    if x_github_event == "ping":
        response.status_code = status.HTTP_200_OK
        logger.info("Received GitHub ping event! Webhook connection verified.")
        return {
            "status": "connected",
            "message": "ConsensusDev Webhook connection verified successfully!",
            "zen": payload.get("zen", ""),
        }

    # 3. Handle Pull Request events
    if x_github_event == "pull_request":
        action = payload.get("action", "")
        pr_data = payload.get("pull_request", {})
        pr_number = pr_data.get("number", 0)
        repo_name = pr_data.get("base", {}).get("repo", {}).get("full_name", "")
        head_sha = pr_data.get("head", {}).get("sha", "")
        delivery_id = x_github_delivery or f"del-{uuid.uuid4().hex[:6]}"

        logger.info(f"Received GitHub PR #{pr_number} action: '{action}' SHA: {head_sha[:7]}")

        # Idempotency deduplication check
        idempotency_key = f"{repo_name}:{pr_number}:{head_sha}:{action}:{delivery_id}"
        existing_review_id = store.is_event_processed(idempotency_key)
        if existing_review_id:
            existing_review = store.get_review(existing_review_id)
            logger.info(f"Duplicate webhook event detected ({idempotency_key}). Returning cached review.")
            response.status_code = status.HTTP_200_OK
            return {
                "status": "already_processed",
                "review_id": existing_review_id,
                "review": existing_review,
            }

        if action in ["opened", "reopened", "synchronize"]:
            request_id = f"req-{uuid.uuid4().hex[:8]}"
            review_id = f"pr-{pr_number}"
            store.record_processed_event(idempotency_key, review_id)

            # Schedule asynchronous processing
            background_tasks.add_task(
                orchestrator.process_pull_request_event,
                pr_data=pr_data,
                request_id=request_id,
            )

            # In development/test if requested synchronous execution or testing directly
            sync_header = request.headers.get("x-consensusdev-sync", "false").lower()
            if sync_header in ["true", "1"]:
                result = await orchestrator.process_pull_request_event(pr_data, request_id=request_id)
                response.status_code = status.HTTP_200_OK
                return {
                    "status": "processed_sync",
                    "action": action,
                    "review": result,
                }

            return {
                "status": "accepted",
                "action": action,
                "pr_number": pr_number,
                "review_id": review_id,
                "request_id": request_id,
                "message": "Review job queued for autonomous execution.",
            }

        return {
            "status": "ignored",
            "action": action,
            "message": f"Action '{action}' does not require automated review gate.",
        }

    return {
        "status": "ignored",
        "event": x_github_event,
        "message": f"Event '{x_github_event}' is not monitored.",
    }


@app.get("/api/pull-requests")
@app.get("/prs")
async def list_pull_requests():
    """
    List all reviewed Pull Requests from the persistent database.
    """
    reviews = store.list_reviews()
    return {
        "total": len(reviews),
        "prs": reviews,
    }


@app.get("/api/pull-requests/{review_id}")
@app.get("/prs/{review_id}")
async def get_pull_request(review_id: str):
    """
    Get detailed canonical ReviewResult for a specific PR or review ID.
    """
    review = store.get_review(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pull Request review '{review_id}' not found",
        )
    return review


@app.post("/api/pull-requests/{review_id}/approve")
async def approve_pull_request(
    review_id: str,
    body: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """
    Human-in-the-loop (HITL) manual approval override for a blocked/rejected PR review.
    """
    review = store.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    approval_id = f"hitl-{uuid.uuid4().hex[:8]}"
    approval_rec = ApprovalEventRecord(
        id=approval_id,
        review_id=review.meta.id,
        actor=body.actor,
        action="approved",
        reason=body.reason,
    )
    db.add(approval_rec)

    # Update review status
    review.consensus.decision = "approved"
    review.status = "APPROVED"
    review.consensus.summary += f" [MANUAL APPROVAL by {body.actor}: {body.reason}]"
    store.save_review(review)

    store.add_log(
        service="Gateway",
        level="WARN",
        message=f"Manual HITL approval override applied to PR #{review.meta.prNumber} by {body.actor}",
        review_id=review.meta.id,
        details={"actor": body.actor, "reason": body.reason, "event": "HITL_OVERRIDE"},
    )

    return {
        "status": "success",
        "message": f"PR #{review.meta.prNumber} manually approved by {body.actor}",
        "review": review,
    }


@app.get("/api/logs")
async def get_audit_logs(limit: int = Query(default=100, ge=1, le=500)):
    """
    Get real structured audit logs with service correlation.
    """
    logs = store.get_logs(limit=limit)
    return {
        "total": len(logs),
        "logs": logs,
    }


@app.get("/api/agents")
async def get_agents_info():
    """
    Returns canonical agent metadata, models, and consensus weights.
    """
    return {
        "agents": [
            {
                "id": "security",
                "name": "Security Auditor",
                "role": "DevSecOps & SAST Scanner",
                "weightPercent": 40,
                "model": os.getenv("SECURITY_AGENT_MODEL", os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")),
                "strictness": "Blocking (Zero critical CVEs)",
                "description": "Detects secrets, infrastructure-as-code misconfigurations, dependency vulnerabilities, and SQLi risks.",
            },
            {
                "id": "tech_debt",
                "name": "Code Quality Reviewer",
                "role": "Technical Debt & Style Guard",
                "weightPercent": 20,
                "model": os.getenv("TECH_DEBT_AGENT_MODEL", os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")),
                "strictness": "Advisory (Cognitive complexity < 10)",
                "description": "Ensures PEP8 adherence, typing completeness, cyclomatic complexity bounds, and clean code hygiene.",
            },
            {
                "id": "story_match",
                "name": "Story / Requirement Reviewer",
                "role": "Requirements & Acceptance Guard",
                "weightPercent": 20,
                "model": os.getenv("STORY_AGENT_MODEL", os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")),
                "strictness": "Blocking (Acceptance Criteria & Test Passes)",
                "description": "Verifies code diffs align with user stories, prevent scope creep, and satisfy QA test criteria.",
            },
            {
                "id": "performance",
                "name": "Performance Reviewer",
                "role": "Computational Complexity & I/O Guard",
                "weightPercent": 20,
                "model": os.getenv("PERFORMANCE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")),
                "strictness": "Advisory (O(1)/O(N) bounds)",
                "description": "Analyzes algorithmic time and space complexity (Big-O), memory leaks, N+1 database queries, and blocking I/O.",
            },
        ]
    }


@app.post("/api/reviews/trigger")
async def trigger_manual_review(request: ManualTriggerRequest):
    """
    Direct endpoint to trigger end-to-end review on a PR diff.
    """
    pr_data = {
        "number": request.pr_number,
        "title": request.title,
        "user": {"login": request.author},
        "head": {"ref": request.branch, "sha": uuid.uuid4().hex},
        "base": {
            "ref": "main",
            "repo": {
                "full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1",
                "owner": {"login": "Ahmed233-GA"},
                "name": "ConsensusDev-hackathon-2026-v1",
            },
        },
        "diff_text": request.diff,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    review = await orchestrator.process_pull_request_event(pr_data)
    return {
        "status": "completed",
        "review": review,
    }