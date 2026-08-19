"""Unit and integration tests for AI Engine agents output validation.

Tests verify:
1. Agent output structure (verdict: pass/fail/error, issues: list of strings)
2. JSON parsing robustness (clean JSON, markdown-wrapped, noisy text, invalid JSON)
3. Exception and timeout handling
4. Multi-agent aggregation (run_all_agents)
5. FastAPI /review and /health endpoints
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from ai_engine.agents.security_agent import review_security, _extract_json as extract_security_json
from ai_engine.agents.performance_agent import review_performance, _extract_json as extract_perf_json
from ai_engine.agents.story_match_agent import review_story_match, _extract_json as extract_story_json
from ai_engine.agents.tech_debt_agent import review_tech_debt, _extract_json as extract_debt_json
from ai_engine.main import app, run_all_agents, ReviewRequest, ReviewResponse, AgentResult


def _mock_completion_response(content: str):
    """Helper to generate a mock litellm completion response."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp


class TestAgentOutputSchema(unittest.TestCase):
    """Verify that each agent produces the correct output schema."""

    @patch("ai_engine.agents.security_agent.litellm.completion")
    def test_security_agent_pass_output(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response('{"verdict": "pass", "issues": []}')
        result = review_security("diff --git a/test.py b/test.py\n+def safe(): pass")

        self.assertIsInstance(result, dict)
        self.assertIn("verdict", result)
        self.assertIn("issues", result)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["issues"], [])

    @patch("ai_engine.agents.security_agent.litellm.completion")
    def test_security_agent_fail_output(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response(
            '{"verdict": "fail", "issues": ["Hardcoded API secret found on line 12"]}'
        )
        result = review_security("diff --git a/app.py b/app.py\n+API_KEY='secret123'")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["verdict"], "fail")
        self.assertIsInstance(result["issues"], list)
        self.assertEqual(len(result["issues"]), 1)
        self.assertIn("Hardcoded API secret", result["issues"][0])

    @patch("ai_engine.agents.performance_agent.litellm.completion")
    def test_performance_agent_output(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response(
            '{"verdict": "fail", "issues": ["Database query executed inside for-loop (N+1 query)"]}'
        )
        result = review_performance("diff --git a/service.py b/service.py\n+for u in users:\n+  db.query(u)")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["verdict"], "fail")
        self.assertIsInstance(result["issues"], list)
        self.assertTrue(any("N+1" in issue for issue in result["issues"]))

    @patch("ai_engine.agents.story_match_agent.litellm.completion")
    def test_story_match_agent_output(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response(
            '{"verdict": "fail", "issues": ["Ticket asked for password reset endpoint, but diff implements user deletion."]}'
        )
        result = review_story_match(
            diff_text="diff --git a/auth.py\n+def delete_user(): pass",
            ticket_description="Implement password reset email token flow"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["verdict"], "fail")
        self.assertIsInstance(result["issues"], list)
        self.assertEqual(len(result["issues"]), 1)

    @patch("ai_engine.agents.tech_debt_agent.litellm.completion")
    def test_tech_debt_agent_output(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response(
            '{"verdict": "pass", "issues": []}'
        )
        result = review_tech_debt("diff --git a/clean.py b/clean.py\n+def pure_add(a, b): return a + b")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["issues"], [])


class TestJSONExtractionAndRobustness(unittest.TestCase):
    """Test extraction of JSON from raw model output under various formatting conditions."""

    def test_extract_clean_json(self):
        raw = '{"verdict": "pass", "issues": []}'
        parsed = extract_security_json(raw)
        self.assertEqual(parsed, {"verdict": "pass", "issues": []})

    def test_extract_json_with_surrounding_whitespace(self):
        raw = '\n\n  {"verdict": "fail", "issues": ["Issue 1"]} \n\n'
        parsed = extract_perf_json(raw)
        self.assertEqual(parsed["verdict"], "fail")
        self.assertEqual(parsed["issues"], ["Issue 1"])

    def test_extract_json_wrapped_in_markdown_fences(self):
        raw = '```json\n{"verdict": "fail", "issues": ["Unchecked input"]}\n```'
        parsed = extract_debt_json(raw)
        self.assertEqual(parsed["verdict"], "fail")
        self.assertEqual(parsed["issues"], ["Unchecked input"])

    def test_extract_json_with_conversational_text(self):
        raw = 'Here is the analysis:\n{"verdict": "pass", "issues": []}\nHope this helps!'
        parsed = extract_story_json(raw)
        self.assertEqual(parsed["verdict"], "pass")
        self.assertEqual(parsed["issues"], [])

    def test_extract_invalid_json_raises_error(self):
        raw = "Sorry, I cannot process this request."
        with self.assertRaises(json.JSONDecodeError):
            extract_security_json(raw)

    @patch("ai_engine.agents.security_agent.litellm.completion")
    def test_agent_handles_invalid_json_gracefully(self, mock_litellm):
        mock_litellm.return_value = _mock_completion_response("Not a JSON response at all")
        result = review_security("diff text")
        self.assertEqual(result["verdict"], "error")
        self.assertIn("Model returned invalid JSON", result["issues"][0])

    @patch("ai_engine.agents.security_agent.litellm.completion")
    def test_agent_handles_llm_exception_gracefully(self, mock_litellm):
        mock_litellm.side_effect = ConnectionError("Failed to connect to Ollama service")
        result = review_security("diff text")
        self.assertEqual(result["verdict"], "error")
        self.assertTrue(any("Agent call failed" in issue for issue in result["issues"]))


class TestMultiAgentRunnerAndFastAPI(unittest.TestCase):
    """Test parallel execution aggregation and FastAPI API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("ai_engine.main.review_security")
    @patch("ai_engine.main.review_performance")
    @patch("ai_engine.main.review_story_match")
    @patch("ai_engine.main.review_tech_debt")
    def test_run_all_agents_all_pass(self, mock_debt, mock_story, mock_perf, mock_sec):
        mock_sec.return_value = {"verdict": "pass", "issues": []}
        mock_perf.return_value = {"verdict": "pass", "issues": []}
        mock_story.return_value = {"verdict": "pass", "issues": []}
        mock_debt.return_value = {"verdict": "pass", "issues": []}

        results = run_all_agents(diff="diff content", ticket="ticket content")

        self.assertEqual(len(results), 4)
        agent_names = {r.agent for r in results}
        self.assertEqual(agent_names, {"security", "performance", "story_match", "tech_debt"})
        self.assertTrue(all(r.verdict == "pass" for r in results))

    @patch("ai_engine.main.review_security")
    @patch("ai_engine.main.review_performance")
    @patch("ai_engine.main.review_story_match")
    @patch("ai_engine.main.review_tech_debt")
    def test_review_endpoint_returns_pass(self, mock_debt, mock_story, mock_perf, mock_sec):
        mock_sec.return_value = {"verdict": "pass", "issues": []}
        mock_perf.return_value = {"verdict": "pass", "issues": []}
        mock_story.return_value = {"verdict": "pass", "issues": []}
        mock_debt.return_value = {"verdict": "pass", "issues": []}

        response = self.client.post("/review", json={
            "diff": "some valid diff",
            "ticket_description": "some ticket"
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["overall_verdict"], "pass")
        self.assertEqual(len(data["agents"]), 4)

    @patch("ai_engine.main.review_security")
    @patch("ai_engine.main.review_performance")
    @patch("ai_engine.main.review_story_match")
    @patch("ai_engine.main.review_tech_debt")
    def test_review_endpoint_returns_fail_when_one_agent_fails(self, mock_debt, mock_story, mock_perf, mock_sec):
        mock_sec.return_value = {"verdict": "fail", "issues": ["SQL injection in auth.py"]}
        mock_perf.return_value = {"verdict": "pass", "issues": []}
        mock_story.return_value = {"verdict": "pass", "issues": []}
        mock_debt.return_value = {"verdict": "pass", "issues": []}

        response = self.client.post("/review", json={
            "diff": "vuln diff",
            "ticket_description": "ticket"
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["overall_verdict"], "fail")
        sec_result = next(a for a in data["agents"] if a["agent"] == "security")
        self.assertEqual(sec_result["verdict"], "fail")
        self.assertIn("SQL injection in auth.py", sec_result["issues"])


if __name__ == "__main__":
    unittest.main()
