"""
Live LLM API Test - Proves the agents call YOUR OpenRouter API token.
"""
import asyncio
import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_engine.agents.security_agent import SecurityAgent
from ai_engine.agents.debt_agent import TechDebtAgent


async def test_live_llm():
    print("=" * 70)
    print("  LIVE LLM API TEST — Calling YOUR OpenRouter API Token")
    print("=" * 70)

    # Show which API key and model are being used
    agent = SecurityAgent()
    print(f"\n[SecurityAgent]")
    print(f"  API Key: {agent.api_key[:20]}...{agent.api_key[-8:]}" if agent.api_key else "  API Key: NOT SET")
    print(f"  Model:   {agent.model_name}")
    print(f"  OpenRouter: {agent.is_openrouter}")

    debt = TechDebtAgent()
    print(f"\n[TechDebtAgent]")
    print(f"  API Key: {debt.api_key[:20]}...{debt.api_key[-8:]}" if debt.api_key else "  API Key: NOT SET")
    print(f"  Model:   {debt.model_name}")

    # Test diff with a SQL injection vulnerability
    test_diff = '''diff --git a/app/db.py b/app/db.py
--- a/app/db.py
+++ b/app/db.py
@@ -1,3 +1,5 @@
+import sqlite3
+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
'''

    print("\n" + "-" * 70)
    print("  Sending test diff to SecurityAgent via OpenRouter LLM...")
    print("-" * 70)

    result = await agent.evaluate(test_diff, context={"security": {}})

    print(f"\n  [OK] RESPONSE FROM LLM:")
    print(f"  Agent:           {result.agent_name}")
    print(f"  Score:           {result.score}/100")
    print(f"  Passed:          {result.passed}")
    print(f"  Feedback:        {result.feedback}")
    print(f"  Critical Issues: {result.critical_issues}")
    print(f"  Suggestions:     {result.suggestions}")

    print("\n" + "-" * 70)
    print("  Sending test diff to TechDebtAgent via OpenRouter LLM...")
    print("-" * 70)

    result2 = await debt.evaluate(test_diff, context={})

    print(f"\n  [OK] RESPONSE FROM LLM:")
    print(f"  Agent:           {result2.agent_name}")
    print(f"  Score:           {result2.score}/100")
    print(f"  Passed:          {result2.passed}")
    print(f"  Feedback:        {result2.feedback}")
    print(f"  Critical Issues: {result2.critical_issues}")
    print(f"  Suggestions:     {result2.suggestions}")

    print("\n" + "=" * 70)
    print("  TEST COMPLETE — Both agents called your OpenRouter LLM directly")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_live_llm())
