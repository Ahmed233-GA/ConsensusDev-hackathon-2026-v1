"""
ConsensusDev — SHA Race Condition Verification
Label: SHA race — simulation (no live GitHub push)
Demonstrates orchestrator guardrail aborting auto-merge when PR head SHA changes during review computation.
"""

import asyncio
import sys
from pathlib import Path

# Add repo root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from gateway.orchestrator import PipelineOrchestrator
from gateway.github_client import GitHubClient


class RaceSimGitHubClient(GitHubClient):
    def __init__(self, initial_sha: str, new_head_sha: str):
        super().__init__(token="mock_token")
        self.initial_sha = initial_sha
        self.new_head_sha = new_head_sha
        self.merged_prs = []

    async def fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        return "diff --git a/app.py b/app.py\n+def add(a, b): return a + b"

    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        # Simulation: while review was computing on initial_sha, a new commit was pushed
        return self.new_head_sha

    async def get_branch_status_checks(self, owner: str, repo: str, sha: str):
        return {"passed": True, "state": "success", "total": 1}

    async def post_pr_review(self, owner: str, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> bool:
        return True

    async def merge_pr(self, owner: str, repo: str, pr_number: int, commit_title: str = "", merge_method: str = "squash") -> bool:
        self.merged_prs.append(pr_number)
        return True


async def main():
    sha_a = "a1b2c3d4e5f678901234567890abcdef12345678"
    sha_b = "b9c8d7e6f5a432109876543210fedcba87654321"

    print("--- [TEST] SHA race -- simulation (no live GitHub push) ---")
    gh = RaceSimGitHubClient(initial_sha=sha_a, new_head_sha=sha_b)
    orch = PipelineOrchestrator(github_client=gh)
    orch.auto_merge_enabled = True

    pr_payload = {
        "number": 888,
        "title": "Fix calculation algorithm",
        "user": {"login": "FastDeveloper"},
        "head": {"ref": "feature/calc", "sha": sha_a},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": "diff --git a/app.py b/app.py\n+def add(a, b): return a + b",
    }

    print(f"reviewed_sha = {sha_a}")
    res = await orch.process_pull_request_event(pr_payload)
    print(f"push detected -> current head = {gh.new_head_sha}")
    print(f"verdict -> {res.consensus.blocking_reasons}")
    print(f"merge -> {'executed' if res.merged else 'aborted'}")


if __name__ == "__main__":
    asyncio.run(main())
