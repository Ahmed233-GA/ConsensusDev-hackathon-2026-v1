import json
import logging
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class StoryAgent(BaseReviewAgent):
    """
    AI Story Match & Functional Reviewer Agent.
    Executes via OpenRouter / Cloud LLM model to verify that code changes
    align with the user story requirements and validates QA test metrics.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="story_match", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)
        qa_payload = context.get("tests", {})
        story_desc = context.get("story_description", "Implement requested feature and fix bugs")

        # System prompt for LLM Model
        system_prompt = (
            "You are a Product Owner and Lead QA Architect reviewing PR diffs against acceptance criteria. "
            "Verify if code aligns with the intended story/objective, does not introduce scope creep, "
            "and has sufficient automated test coverage based on the QA report. "
            "You MUST respond ONLY with valid JSON in this exact structure:\n"
            "{\n"
            '  "score": <integer from 0 to 100>,\n'
            '  "passed": <boolean: true if satisfies requirements and test criteria (score >= 75), false otherwise>,\n'
            '  "feedback": "<concise summary of story match and QA validation>",\n'
            '  "critical_issues": ["<acceptance issue 1>"],\n'
            '  "suggestions": ["<test or story improvement 1>"]\n'
            "}"
        )

        user_prompt = (
            f"User Story / PR Intent:\n{story_desc}\n\n"
            f"PR Diff:\n```diff\n{diff}\n```\n\n"
            f"QA Runner (Pytest/Coverage) Report:\n{json.dumps(qa_payload, indent=2)}\n\n"
            "Analyze requirement match and return JSON."
        )

        # 1. Execute LLM Model Call via OpenRouter
        llm_response = await self.call_llm(system_prompt, user_prompt)
        if llm_response and "score" in llm_response:
            score = int(llm_response.get("score", 90))
            passed = bool(llm_response.get("passed", score >= 75))
            feedback = str(llm_response.get("feedback", "Satisfies user story requirements with adequate test validation"))

            return AgentEvaluation(
                agent_name=self.name,
                score=score,
                passed=passed,
                feedback=feedback,
                critical_issues=list(llm_response.get("critical_issues", [])),
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # 2. Fallback when running offline without API keys
        return self._heuristic_analysis(diff_meta, qa_payload, story_desc)

    def _heuristic_analysis(
        self, diff_meta: Dict[str, Any], qa_payload: Dict[str, Any], story_desc: str
    ) -> AgentEvaluation:
        issues: List[str] = []
        suggestions: List[str] = []
        score = 90

        qa_status = qa_payload.get("status", "").upper()
        tests_failed = qa_payload.get("tests_failed", 0)
        coverage_pct = qa_payload.get("coverage_percentage", None)

        if qa_status == "FAIL" or tests_failed > 0:
            score -= 40
            issues.append(f"QA test suite failed with {tests_failed} failing tests")
        elif coverage_pct is not None and coverage_pct < 50.0:
            score -= 25
            issues.append(f"Low test coverage ({coverage_pct}% is below minimum 50%)")
            suggestions.append("Add unit tests to cover newly added logic.")

        has_tests_in_diff = any(
            "test" in f.lower() or f.endswith("_test.py") or f.startswith("test_")
            for f in diff_meta["files_changed"]
        )
        if not has_tests_in_diff and diff_meta["total_additions"] > 25 and coverage_pct is None:
            score -= 15
            suggestions.append("PR introduces non-trivial logic without any test file updates.")

        score = max(0, min(100, score))
        passed = score >= 75 and tests_failed == 0

        if passed:
            feedback = "Satisfies user story requirements with adequate test validation"
        else:
            feedback = f"Story/QA criteria not met: {'; '.join(issues) if issues else 'Insufficient test coverage'}"

        return AgentEvaluation(
            agent_name=self.name,
            score=score,
            passed=passed,
            feedback=feedback,
            critical_issues=issues,
            suggestions=suggestions,
        )
