import asyncio
import logging
import os
from typing import Optional, Set
from gateway.github_client import GitHubClient
from gateway.orchestrator import PipelineOrchestrator
from gateway.store import store

logger = logging.getLogger("gateway.poller")


class GitHubPoller:
    """
    Background polling loop for detecting new Pull Requests on the target GitHub repository.
    Periodically checks for open PRs, performs idempotency checks, and triggers the
    full multi-agent review and auto-merge pipeline.
    """

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        github_client: Optional[GitHubClient] = None,
        poll_interval: Optional[int] = None,
    ):
        self.orchestrator = orchestrator
        self.github_client = github_client or GitHubClient()
        self.poll_interval = poll_interval or int(os.getenv("GITHUB_POLL_INTERVAL", "5"))
        self.enabled = os.getenv("GITHUB_POLLING_ENABLED", "true").lower() in ["1", "true", "yes"]
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._processed_keys: Set[str] = set()

    def _get_idempotency_key(self, owner: str, repo: str, pr_number: int, head_sha: str) -> str:
        return f"{owner}/{repo}#{pr_number}@{head_sha}"

    def is_processed(self, owner: str, repo: str, pr_number: int, head_sha: str) -> bool:
        key = self._get_idempotency_key(owner, repo, pr_number, head_sha)
        if key in self._processed_keys:
            return True
        # Check SQLite Review Store
        existing_rev = store.get_review(f"pr-{pr_number}") or store.get_review(str(pr_number))
        if existing_rev and existing_rev.meta.commitSha == head_sha:
            self._processed_keys.add(key)
            return True
        return False

    def mark_processed(self, owner: str, repo: str, pr_number: int, head_sha: str):
        key = self._get_idempotency_key(owner, repo, pr_number, head_sha)
        self._processed_keys.add(key)

    async def poll_once(self):
        owner = os.getenv("GITHUB_REPO_OWNER", "Ahmed233-GA")
        repo = os.getenv("GITHUB_REPO_NAME", "consensusdev-live-demo")
        token = os.getenv("GITHUB_TOKEN", "")

        if not token or token.startswith("ghp_your_"):
            logger.debug("GitHub token not configured or default placeholder; skipping polling tick.")
            return

        try:
            open_prs = await self.github_client.list_open_prs(owner, repo)
            if not open_prs:
                return

            for pr in open_prs:
                pr_number = pr.get("number")
                if not pr_number:
                    continue

                head_sha = pr.get("head", {}).get("sha", "")
                if self.is_processed(owner, repo, pr_number, head_sha):
                    continue

                logger.info(f"⚡ [Poller] Detected NEW open PR #{pr_number} on {owner}/{repo} (SHA: {head_sha[:7]})")

                # Format payload to match standard GitHub PR webhook event structure
                pr_event = {
                    "number": pr_number,
                    "title": pr.get("title", f"Pull Request #{pr_number}"),
                    "user": {"login": pr.get("user", {}).get("login", "Developer")},
                    "head": {
                        "ref": pr.get("head", {}).get("ref", "feature/branch"),
                        "sha": head_sha,
                    },
                    "base": {
                        "ref": pr.get("base", {}).get("ref", "main"),
                        "repo": {
                            "full_name": f"{owner}/{repo}",
                            "owner": {"login": owner},
                            "name": repo,
                        },
                    },
                    "html_url": pr.get("html_url", ""),
                }

                # Mark as processed upfront to prevent race conditions
                self.mark_processed(owner, repo, pr_number, head_sha)

                try:
                    review = await self.orchestrator.process_pull_request_event(pr_event)
                    logger.info(
                        f"✅ [Poller] Completed review for PR #{pr_number}. "
                        f"Decision: {review.consensus.decision.upper()} (Score: {review.consensus.score}/100)"
                    )
                except Exception as ex:
                    logger.error(f"❌ [Poller] Failed processing PR #{pr_number}: {ex}")

        except Exception as e:
            logger.error(f"Error during GitHub polling cycle: {e}")

    async def start(self):
        if not self.enabled:
            logger.info("GitHub polling is disabled (GITHUB_POLLING_ENABLED=false).")
            return

        self._running = True
        logger.info(
            f"🚀 [Poller] Started GitHub polling service (Interval: {self.poll_interval}s, "
            f"Target: {os.getenv('GITHUB_REPO_OWNER', 'Ahmed233-GA')}/{os.getenv('GITHUB_REPO_NAME', 'consensusdev-live-demo')})"
        )
        while self._running:
            try:
                await self.poll_once()
            except Exception as e:
                logger.error(f"Unexpected error in GitHub poll loop: {e}")

            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("GitHub polling service stopped.")
