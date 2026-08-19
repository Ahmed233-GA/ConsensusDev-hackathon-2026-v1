import logging
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from gateway.github_client import GitHubClient
from gateway.orchestrator import PipelineOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-Gateway")

# Load .env if present
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

app = FastAPI(
    title="ConsensusDev Gateway",
    description="Central Orchestration Gateway & GitHub Automation Service (Port 8000)",
    version="1.0.0",
)

github_client = GitHubClient()
orchestrator = PipelineOrchestrator(github_client=github_client)


@app.get("/")
async def root():
    return {
        "service": "ConsensusDev Gateway",
        "port": 8000,
        "status": "running",
        "version": "1.0.0",
        "webhook_endpoint": "/webhook/github",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "gateway": "online",
            "orchestration": "ready",
        },
    }


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default="pull_request"),
    x_hub_signature_256: str = Header(default=None),
):
    """
    GitHub Webhook receiver.
    Intercepts Pull Request events (opened, synchronize, reopened)
    and initiates the ConsensusDev 5-service autonomous review pipeline.
    """
    payload_body = await request.body()
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")

    # 1. Verify Signature
    if webhook_secret and not github_client.verify_webhook_signature(
        payload_body, x_hub_signature_256, webhook_secret
    ):
        logger.warning("Invalid GitHub webhook signature received.")
        raise HTTPException(status_code=401, detail="Invalid HMAC-SHA256 signature")

    payload = await request.json()

    # 2. Handle GitHub ping test event
    if x_github_event == "ping":
        logger.info("Received GitHub ping event! Webhook is successfully connected.")
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

        logger.info(f"Received GitHub PR #{pr_number} action: '{action}'")

        # Process when PR is opened, reopened, or new commits pushed (synchronize)
        if action in ["opened", "reopened", "synchronize"]:
            # Run orchestration synchronously or schedule in background
            result = await orchestrator.process_pull_request_event(pr_data)
            return {
                "status": "processed",
                "action": action,
                "orchestration_result": result,
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