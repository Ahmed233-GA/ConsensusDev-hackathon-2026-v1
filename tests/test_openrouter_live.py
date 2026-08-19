import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_engine.agents.security_agent import SecurityAgent
from ai_engine.agents.debt_agent import TechDebtAgent
from ai_engine.agents.story_agent import StoryAgent
from ai_engine.agents.perf_agent import PerformanceAgent
from ai_engine.services.review_service import ReviewService
from ai_engine.schemas import AnalyzePRRequest


async def main():
    print("=" * 70)
    print("[ConsensusDev AI Engine] Live Model Connectivity Test")
    print("=" * 70)

    # Instantiate agents
    sec = SecurityAgent()
    debt = TechDebtAgent()
    story = StoryAgent()
    perf = PerformanceAgent()

    agents = [
        ("Security Agent", sec),
        ("Tech Debt Agent", debt),
        ("Story Match Agent", story),
        ("Performance Agent", perf),
    ]

    for label, agent in agents:
        key_masked = (
            f"{agent.api_key[:8]}...{agent.api_key[-4:]}"
            if agent.api_key and len(agent.api_key) > 12
            else ("NOT CONFIGURED (Using local heuristics)" if not agent.api_key else agent.api_key)
        )
        provider = "OpenRouter Cloud LLM" if agent.is_openrouter else ("OpenAI Cloud LLM" if agent.api_key else "Local Heuristic Engine")
        print(f"\n[{label}]")
        print(f"  * Model:    {agent.model_name}")
        print(f"  * Provider: {provider}")
        print(f"  * API Key:  {key_masked}")

    print("\n" + "=" * 70)
    print("[INFO] Sending Sample PR Diff to the 4 AI Agents...")
    print("=" * 70)

    sample_diff = """diff --git a/app/user_service.py b/app/user_service.py
index 100644..100644
--- a/app/user_service.py
+++ b/app/user_service.py
@@ -1,5 +1,8 @@
-def find_user(user_id):
-    return None
+def find_user(user_id: int):
+    query = "SELECT * FROM users WHERE id = :id"
+    return db.fetch_one(query, {"id": user_id})
"""

    service = ReviewService()
    req = AnalyzePRRequest(
        diff=sample_diff,
        security={"status": "PASS", "vulnerabilities_count": 0, "critical_issues": []},
        tests={"status": "PASS", "tests_passed": 10, "coverage_percentage": 92.0},
        pr_number=142,
    )

    response = await service.analyze_pr(req)

    print(f"\n>>> Consensus Result: {'APPROVED (TRUE) [OK]' if response.consensus else 'BLOCKED (FALSE) [X]'}")
    print(f">>> Overall Score:    {response.score}/100")
    print(f">>> Summary:          {response.summary}\n")
    print("Feedback from the 4 Agents:")
    for k, v in response.agents_feedback.items():
        print(f"  - {k.replace('_', ' ').title()}: {v}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
