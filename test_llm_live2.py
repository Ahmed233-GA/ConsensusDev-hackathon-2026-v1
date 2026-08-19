import io, sys, asyncio, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from ai_engine.agents.security_agent import SecurityAgent
from ai_engine.agents.perf_agent import PerformanceAgent

diff = """diff --git a/app/main.py b/app/main.py
+++ b/app/main.py
+import os
+import subprocess
+def run_command(cmd):
+    os.system(cmd)
+    password = "SuperSecret123"
+    api_key = "AKIA1234567890ABCDEF"
+    for user in users:
+        for item in user.items:
+            result = db.query("SELECT * FROM orders WHERE id=" + str(item.id))
"""

async def main():
    print("=" * 60)
    print("  LIVE TEST #2 - Different diff, check OpenRouter Activity")
    print("=" * 60)

    sec = SecurityAgent()
    perf = PerformanceAgent()

    print(f"\n  Using API Key: {sec.api_key[:15]}...{sec.api_key[-6:]}")
    print(f"  Security Model: {sec.model_name}")
    print(f"  Perf Model: {perf.model_name}")

    print("\n--- Calling SecurityAgent via OpenRouter ---")
    r1 = await sec.evaluate(diff, {"security": {}})
    print(f"  Score:    {r1.score}/100")
    print(f"  Passed:   {r1.passed}")
    print(f"  Feedback: {r1.feedback}")
    print(f"  Issues:   {r1.critical_issues}")

    print("\n--- Calling PerformanceAgent via OpenRouter ---")
    r2 = await perf.evaluate(diff, {})
    print(f"  Score:    {r2.score}/100")
    print(f"  Passed:   {r2.passed}")
    print(f"  Feedback: {r2.feedback}")
    print(f"  Issues:   {r2.critical_issues}")

    print("\n" + "=" * 60)
    print("  DONE - Now check Activity tab on OpenRouter dashboard!")
    print("=" * 60)

asyncio.run(main())
