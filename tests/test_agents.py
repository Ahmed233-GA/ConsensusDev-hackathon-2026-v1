import pytest
from ai_engine.agents.security_agent import SecurityAgent
from ai_engine.agents.debt_agent import TechDebtAgent
from ai_engine.agents.story_agent import StoryAgent
from ai_engine.agents.perf_agent import PerformanceAgent


@pytest.mark.asyncio
async def test_security_agent_detects_sqli():
    agent = SecurityAgent()
    bad_diff = """diff --git a/app/db.py b/app/db.py
index 1234567..89abcdef 100644
--- a/app/db.py
+++ b/app/db.py
@@ -10,3 +10,3 @@
-def get_user(user_id):
+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
"""
    result = await agent.evaluate(bad_diff, context={})
    assert result.passed is False
    assert result.score < 80
    assert any("SQL Injection" in issue for issue in result.critical_issues)


@pytest.mark.asyncio
async def test_security_agent_passes_clean_code():
    agent = SecurityAgent()
    clean_diff = """diff --git a/app/db.py b/app/db.py
index 1234567..89abcdef 100644
--- a/app/db.py
+++ b/app/db.py
@@ -10,3 +10,3 @@
-def get_user(user_id):
+def get_user(user_id: int):
+    query = "SELECT * FROM users WHERE id = :id"
+    return db.execute(query, {"id": user_id})
"""
    result = await agent.evaluate(clean_diff, context={"security": {"status": "PASS"}})
    assert result.passed is True
    assert result.score >= 80
    assert len(result.critical_issues) == 0


@pytest.mark.asyncio
async def test_tech_debt_agent_flags_bare_except_and_prints():
    agent = TechDebtAgent()
    messy_diff = """diff --git a/app/service.py b/app/service.py
index 1234567..89abcdef 100644
--- a/app/service.py
+++ b/app/service.py
@@ -5,3 +5,6 @@
+def do_something():
+    print("debugging here")
+    try:
+        pass
+    except:
+        pass
"""
    result = await agent.evaluate(messy_diff, context={})
    assert len(result.critical_issues) >= 1
    assert any("except" in issue.lower() or "print" in issue.lower() for issue in result.critical_issues)


@pytest.mark.asyncio
async def test_story_agent_validates_qa_report():
    agent = StoryAgent()
    diff = """diff --git a/app/calc.py b/app/calc.py
+++ b/app/calc.py
@@ -1,1 +1,2 @@
+def add(a: int, b: int) -> int:
+    return a + b
"""
    # Case 1: QA Passed
    passed_qa_context = {
        "story_description": "Implement a simple addition function.",
        "tests": {
            "status": "PASS",
            "tests_passed": 12,
            "tests_failed": 0,
            "coverage_percentage": 95.0,
        }
    }
    res_pass = await agent.evaluate(diff, passed_qa_context)
    assert res_pass.passed is True
    assert res_pass.score >= 75

    # Case 2: QA Failed
    failed_qa_context = {
        "tests": {
            "status": "FAIL",
            "tests_passed": 2,
            "tests_failed": 5,
            "coverage_percentage": 20.0,
        }
    }
    res_fail = await agent.evaluate(diff, failed_qa_context)
    assert res_fail.passed is False


@pytest.mark.asyncio
async def test_perf_agent_flags_nested_loops_and_db_in_loop():
    agent = PerformanceAgent()
    slow_diff = """diff --git a/app/batch.py b/app/batch.py
+++ b/app/batch.py
@@ -1,1 +1,5 @@
+def process_items(items, groups):
+    for item in items:
+        for group in groups:
+            db.query(f"SELECT * FROM group_items WHERE id = {item.id}")
"""
    result = await agent.evaluate(slow_diff, context={})
    assert any("Nested loop" in issue or "N+1" in issue for issue in result.critical_issues)
    assert result.score < 80
