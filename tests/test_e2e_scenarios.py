import hashlib
import hmac
import json
import pytest
from httpx import ASGITransport, AsyncClient

from gateway.main import app
from gateway.orchestrator import PipelineOrchestrator
from gateway.github_client import GitHubClient


class MockGitHubClient(GitHubClient):
    def __init__(
        self,
        should_fail_review: bool = False,
        should_fail_checks: bool = False,
        current_sha: str = "sha_abc",
    ):
        super().__init__(token="mock_token")
        self.should_fail_review = should_fail_review
        self.should_fail_checks = should_fail_checks
        self.current_sha = current_sha
        self.reviews_posted = []
        self.merged_prs = []

    async def fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        return ""

    async def get_pr_head_sha(self, owner: str, repo: str, pr_number: int) -> str:
        return self.current_sha

    async def get_branch_status_checks(self, owner: str, repo: str, sha: str):
        if self.should_fail_checks:
            return {"passed": False, "state": "failure", "total": 2}
        return {"passed": True, "state": "success", "total": 2}

    async def post_pr_review(
        self, owner: str, repo: str, pr_number: int, body: str, event: str = "COMMENT"
    ) -> bool:
        if self.should_fail_review:
            return False
        self.reviews_posted.append({"pr_number": pr_number, "event": event, "body": body})
        return True

    async def merge_pr(
        self, owner: str, repo: str, pr_number: int, commit_title: str = "", merge_method: str = "squash"
    ) -> bool:
        self.merged_prs.append(pr_number)
        return True


@pytest.mark.asyncio
async def test_scenario_a_clean_pr(monkeypatch):
    """
    Scenario A: Clean PR -> Passes Scanner, QA, AI -> Approved for Auto-Merge
    """
    mock_gh = MockGitHubClient(current_sha="commit_clean_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,3 +1,3 @@
+def add(a: int, b: int) -> int:
+    return a + b
"""
    pr_data = {
        "number": 201,
        "title": "Add addition calculation utility",
        "user": {"login": "CleanDev"},
        "head": {"ref": "feature/calc", "sha": "commit_clean_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.consensus.decision == "approved"
    assert result.consensus.score >= 80
    assert result.consensus.gates.security == "passed"
    assert result.consensus.gates.qa == "passed"
    assert result.merged is True
    assert 201 in mock_gh.merged_prs


@pytest.mark.asyncio
async def test_scenario_b_critical_vulnerability(monkeypatch):
    """
    Scenario B: Malicious PR with SQLi & Hardcoded API Key -> Blocked
    """
    mock_gh = MockGitHubClient(current_sha="commit_bad_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    vuln_diff = """diff --git a/app/auth.py b/app/auth.py
+++ b/app/auth.py
@@ -1,5 +1,6 @@
+api_key = "sk-1234567890abcdef1234567890abcdef"
+query = f"SELECT * FROM accounts WHERE user = '{user_input}'"
"""
    pr_data = {
        "number": 202,
        "title": "Quick auth patch",
        "user": {"login": "HackerDev"},
        "head": {"ref": "feature/hack", "sha": "commit_bad_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": vuln_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.consensus.decision == "rejected"
    assert result.consensus.gates.security == "failed"
    assert result.merged is False
    assert 202 not in mock_gh.merged_prs
    assert any("CRITICAL" in r or "SECURITY" in r for r in result.consensus.blocking_reasons)


@pytest.mark.asyncio
async def test_scenario_c_scanner_offline(monkeypatch):
    """
    Scenario C: Security Scanner is offline -> Fail-Closed Blocked
    """
    mock_gh = MockGitHubClient(current_sha="commit_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.security_url = "http://localhost:59999/scan"
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 203,
        "title": "Clean PR but scanner offline",
        "user": {"login": "Dev"},
        "head": {"ref": "feature/calc", "sha": "commit_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.consensus.decision == "rejected"
    assert result.consensus.gates.security == "unknown"
    assert result.merged is False
    assert 203 not in mock_gh.merged_prs


@pytest.mark.asyncio
async def test_scenario_d_qa_offline(monkeypatch):
    """
    Scenario D: QA Runner is offline -> Fail-Closed Blocked
    """
    mock_gh = MockGitHubClient(current_sha="commit_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.qa_url = "http://localhost:59998/run-tests"
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 204,
        "title": "Clean PR but QA offline",
        "user": {"login": "Dev"},
        "head": {"ref": "feature/calc", "sha": "commit_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.consensus.decision == "rejected"
    assert result.consensus.gates.qa == "unknown"
    assert result.merged is False
    assert 204 not in mock_gh.merged_prs


@pytest.mark.asyncio
async def test_scenario_e_stale_sha_mismatch(monkeypatch):
    """
    Scenario E: PR Head SHA changed during review (SHA A was analyzed, but GitHub currently has SHA B) -> No Merge
    """
    mock_gh = MockGitHubClient(current_sha="new_commit_456")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 205,
        "title": "PR with race condition commit push",
        "user": {"login": "FastPusher"},
        "head": {"ref": "feature/fast", "sha": "commit_old_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.merged is False
    assert 205 not in mock_gh.merged_prs
    assert "STALE_REVIEW_SHA_MISMATCH" in result.consensus.blocking_reasons


@pytest.mark.asyncio
async def test_scenario_f_github_review_failure(monkeypatch):
    """
    Scenario F: GitHub review post fails -> Abort Auto-Merge
    """
    mock_gh = MockGitHubClient(should_fail_review=True, current_sha="commit_clean_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 206,
        "title": "PR review post fails",
        "user": {"login": "Dev"},
        "head": {"ref": "feature/calc", "sha": "commit_clean_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.merged is False
    assert 206 not in mock_gh.merged_prs
    assert "REVIEW_POST_FAILED" in result.consensus.blocking_reasons


@pytest.mark.asyncio
async def test_scenario_g_github_checks_failed(monkeypatch):
    """
    Scenario G: Required GitHub branch status check fails -> Auto-Merge Blocked
    """
    mock_gh = MockGitHubClient(should_fail_checks=True, current_sha="commit_clean_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 207,
        "title": "PR with failing GitHub check",
        "user": {"login": "Dev"},
        "head": {"ref": "feature/calc", "sha": "commit_clean_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.merged is False
    assert 207 not in mock_gh.merged_prs
    assert "GITHUB_CHECKS_FAILED" in result.consensus.blocking_reasons


@pytest.mark.asyncio
async def test_scenario_h_ai_offline(monkeypatch):
    """
    Scenario H: AI Consensus Engine is offline/fails -> Auto-Merge Blocked
    """
    mock_gh = MockGitHubClient(current_sha="commit_clean_123")
    orch = PipelineOrchestrator(github_client=mock_gh)
    orch.auto_merge_enabled = True

    async def mock_failed_ai(diff, sec, qa, pr_num):
        return {
            "consensus": False,
            "score": 0,
            "agents_feedback": {},
            "summary": "AI Outage",
            "details": {"blocking_reasons": ["AI_EVIDENCE_UNAVAILABLE"], "gates": {"evidence": "incomplete"}},
        }

    orch.call_ai_engine = mock_failed_ai

    clean_diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,2 +1,2 @@
+def add(a: int, b: int) -> int: return a + b
"""
    pr_data = {
        "number": 208,
        "title": "Clean PR but AI is down",
        "user": {"login": "Dev"},
        "head": {"ref": "feature/calc", "sha": "commit_clean_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": clean_diff,
    }

    result = await orch.process_pull_request_event(pr_data)
    assert result.consensus.decision == "rejected"
    assert result.merged is False
    assert 208 not in mock_gh.merged_prs
    assert "AI_EVIDENCE_UNAVAILABLE" in result.consensus.blocking_reasons


@pytest.mark.asyncio
async def test_scenario_i_duplicate_webhook_deduplication(monkeypatch):
    """
    Scenario I: Duplicate webhook delivery -> Deduplicated without re-running or duplicate merge
    """
    monkeypatch.setenv("WEBHOOK_SECRET", "test_secret_i")
    secret = "test_secret_i"
    payload_dict = {
        "action": "opened",
        "number": 209,
        "pull_request": {
            "number": 209,
            "title": "Idempotency Scenario I",
            "head": {"ref": "feature/idem", "sha": "sha_delivery_999"},
            "base": {
                "ref": "main",
                "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"},
            },
            "user": {"login": "AhmedDev"},
        },
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        body = json.dumps(payload_dict).encode()
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers = {
            "x-github-event": "pull_request",
            "x-hub-signature-256": sig,
            "x-github-delivery": "delivery-unique-999",
            "x-consensusdev-sync": "true",
        }

        # 1st Delivery
        res1 = await client.post("/webhook/github", content=body, headers=headers)
        assert res1.status_code == 200
        assert res1.json()["status"] in ["processed_sync", "accepted"]

        # 2nd Delivery (same delivery ID and SHA)
        res2 = await client.post("/webhook/github", content=body, headers=headers)
        assert res2.status_code == 200
        assert res2.json()["status"] == "already_processed"
