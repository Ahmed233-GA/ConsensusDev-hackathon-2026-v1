import asyncio
import httpx
import pytest
from gateway.orchestrator import PipelineOrchestrator
from gateway.github_client import GitHubClient


class MockGH(GitHubClient):
    def __init__(self):
        super().__init__(token="mock")
        self.merged = []

    async def fetch_pr_diff(self, owner, repo, pr_number):
        return "+ def sample(): pass"

    async def get_pr_head_sha(self, owner, repo, pr_number):
        return "sha_123"

    async def get_branch_status_checks(self, owner, repo, sha):
        return {"passed": True}

    async def post_pr_review(self, owner, repo, pr_number, body, event="COMMENT"):
        return True

    async def merge_pr(self, owner, repo, pr_number, commit_title="", merge_method="squash"):
        self.merged.append(pr_number)
        return True


@pytest.mark.asyncio
async def test_failure_injection_scanner_offline():
    gh = MockGH()
    orch = PipelineOrchestrator(github_client=gh)
    # Inject offline port for scanner
    orch.security_url = "http://127.0.0.1:59999/scan"
    orch.auto_merge_enabled = True

    pr_payload = {
        "number": 501,
        "title": "Clean PR but Scanner Offline",
        "user": {"login": "Dev"},
        "head": {"ref": "feat", "sha": "sha_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev"}},
        "diff_text": "+ def add(a, b): return a + b",
    }

    res = await orch.process_pull_request_event(pr_payload)
    assert res.consensus.decision == "rejected"
    assert res.consensus.gates.security == "unknown"
    assert res.merged is False
    assert 501 not in gh.merged
    assert any("SECURITY" in r for r in res.consensus.blocking_reasons)


@pytest.mark.asyncio
async def test_failure_injection_qa_offline():
    gh = MockGH()
    orch = PipelineOrchestrator(github_client=gh)
    # Inject offline port for QA
    orch.qa_url = "http://127.0.0.1:59998/run-tests"
    orch.auto_merge_enabled = True

    pr_payload = {
        "number": 502,
        "title": "Clean PR but QA Offline",
        "user": {"login": "Dev"},
        "head": {"ref": "feat", "sha": "sha_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev"}},
        "diff_text": "+ def add(a, b): return a + b",
    }

    res = await orch.process_pull_request_event(pr_payload)
    assert res.consensus.decision == "rejected"
    assert res.consensus.gates.qa == "unknown"
    assert res.merged is False
    assert 502 not in gh.merged
    assert any("QA" in r for r in res.consensus.blocking_reasons)


@pytest.mark.asyncio
async def test_failure_injection_ai_offline():
    gh = MockGH()
    orch = PipelineOrchestrator(github_client=gh)
    # Inject offline port for AI Engine and invalid fallback
    orch.ai_url = "http://127.0.0.1:59997/analyze-pr"
    orch.auto_merge_enabled = True

    # Monkeypatch in-process AI to simulate full AI outage
    async def broken_ai(diff, sec, qa, pr_num):
        return {
            "consensus": False,
            "score": 0,
            "agents_feedback": {},
            "summary": "AI Outage",
            "details": {"blocking_reasons": ["AI_EVIDENCE_UNAVAILABLE"], "gates": {"evidence": "incomplete"}},
        }

    orch.call_ai_engine = broken_ai

    pr_payload = {
        "number": 503,
        "title": "Clean PR but AI Offline",
        "user": {"login": "Dev"},
        "head": {"ref": "feat", "sha": "sha_123"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev"}},
        "diff_text": "+ def add(a, b): return a + b",
    }

    res = await orch.process_pull_request_event(pr_payload)
    assert res.consensus.decision == "rejected"
    assert res.merged is False
    assert 503 not in gh.merged
    assert "AI_EVIDENCE_UNAVAILABLE" in res.consensus.blocking_reasons
