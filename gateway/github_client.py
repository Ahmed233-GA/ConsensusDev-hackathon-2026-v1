import hashlib
import hmac
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub REST API client for ConsensusDev Gateway.
    Handles fetching PR diffs, creating review comments, merging PRs,
    and programmatically managing webhooks.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ConsensusDev-Gateway",
        }
        if self.token and not self.token.startswith("ghp_your_"):
            self.headers["Authorization"] = f"token {self.token}"

    def verify_webhook_signature(self, payload_body: bytes, signature_header: Optional[str], secret: str) -> bool:
        """
        Verify GitHub HMAC-SHA256 webhook signature.
        """
        if not signature_header or not secret:
            return True  # Bypass in dev/mock mode if no secret configured

        if not signature_header.startswith("sha256="):
            return False

        expected_signature = "sha256=" + hmac.new(
            secret.encode("utf-8"), payload_body, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature_header)

    async def fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Fetch the unified git diff of a pull request.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=diff_headers)
            if resp.status_code == 200:
                return resp.text
            logger.error(f"Failed to fetch PR #{pr_number} diff: HTTP {resp.status_code} {resp.text}")
            return ""

    async def post_pr_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",  # "APPROVE", "REQUEST_CHANGES", "COMMENT"
    ) -> bool:
        """
        Post a review comment or verdict on a Pull Request.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "body": body,
            "event": event,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            if resp.status_code in [200, 201]:
                logger.info(f"Successfully posted PR #{pr_number} review ({event})")
                return True
            logger.error(f"Failed to post PR #{pr_number} review: HTTP {resp.status_code} {resp.text}")
            return False

    async def merge_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_title: str = "Auto-merged by ConsensusDev Gate",
        merge_method: str = "squash",  # "merge", "squash", "rebase"
    ) -> bool:
        """
        Auto-merge a pull request.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        payload = {
            "commit_title": commit_title,
            "merge_method": merge_method,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(url, headers=self.headers, json=payload)
            if resp.status_code == 200:
                logger.info(f"Successfully auto-merged PR #{pr_number}")
                return True
            logger.error(f"Failed to auto-merge PR #{pr_number}: HTTP {resp.status_code} {resp.text}")
            return False

    async def register_webhook(
        self,
        owner: str,
        repo: str,
        webhook_url: str,
        secret: str = "",
        events: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Programmatically create a GitHub Webhook on the specified repository.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/hooks"
        events = events or ["pull_request", "push", "ping"]
        payload = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0",
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            if resp.status_code in [200, 201]:
                data = resp.json()
                return {"success": True, "hook_id": data.get("id"), "url": webhook_url}
            return {
                "success": False,
                "status_code": resp.status_code,
                "error": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            }
