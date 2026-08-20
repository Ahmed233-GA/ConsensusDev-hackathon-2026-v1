"""
ConsensusDev — Live Demonstration Script
Runs a simulated live end-to-end evaluation through the Gateway.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from gateway.models.review import PullRequestReview
from gateway.orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ConsensusDev-Demo")


async def main():
    print("=" * 70)
    print("  CONSENSUS DEV — LIVE END-TO-END DEMO EVALUATION")
    print("=" * 70)

    orch = PipelineOrchestrator()

    # Sample diff representing clean security and high test quality
    diff_text = """diff --git a/services/auth_validator.py b/services/auth_validator.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/services/auth_validator.py
@@ -0,0 +1,12 @@
+import secrets
+from typing import Optional
+
+def validate_session_token(token: Optional[str]) -> bool:
+    if not token or len(token) < 32:
+        return False
+    # Constant-time comparison for security
+    return secrets.compare_digest(token, token)
+"""

    pr_payload = {
        "number": 142,
        "title": "feat(auth): add constant-time session token validator",
        "user": {"login": "AhmedSoliman"},
        "head": {"ref": "feature/token-validator", "sha": "a1b2c3d4e5f67890abcdef1234567890abcdef12"},
        "base": {"ref": "main", "repo": {"full_name": "Ahmed233-GA/ConsensusDev-hackathon-2026-v1"}},
        "diff_text": diff_text,
    }

    print("\n[*] Processing Pull Request #142 through Multi-Agent Consensus Pipeline...")
    review: PullRequestReview = await orch.process_pull_request_event(pr_payload)

    print("\n" + "=" * 70)
    print("  CONSENSUS REVIEW VERDICT")
    print("=" * 70)
    print(f"PR Number:       #{review.meta.prNumber}")
    print(f"PR Title:        {review.meta.title}")
    print(f"Author:          @{review.meta.author.username}")
    print(f"Consensus Score: {review.consensus.score} / 100")
    print(f"Decision:        {review.consensus.decision.upper()}")
    print(f"Security Gate:   {review.consensus.gates.security.upper()}")
    print(f"QA Gate:         {review.consensus.gates.qa.upper()}")
    print(f"Evidence Gate:   {review.consensus.gates.evidence.upper()}")
    print(f"Review Latency:  {review.reviewTimeSeconds}s")
    print("\n[Agents Breakdown]")
    for agent in review.agents:
        score_val = f"{agent.score}/10" if agent.score is not None else agent.status.upper()
        print(f" - {agent.agentName:<28} (Weight: {agent.weightPercent}%): {score_val}")

    print("\n[Security & QA Findings]")
    print(f" - Security Findings: {len(review.findings)}")
    print(f" - Tests Passed:     {review.qaStats.testsPassed}")
    print(f" - Code Coverage:    {review.qaStats.coveragePercentage}%")
    print(f" - Mutation Score:   {review.qaStats.mutationScore}%")
    print("=" * 70)
    print(" [OK] Live Demonstration Complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
