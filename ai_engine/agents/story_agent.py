import logging
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class StoryAgent(BaseReviewAgent):
    """
    AI Story Match & Functional Reviewer Agent.
    Evaluates whether the PR changes align with expected user stories/PR description
    and checks whether adequate test coverage/results exist (from Shahd's QA service).
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="story_match", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)
        qa_payload = context.get("tests", {})
        story_desc = context.get("story_description", "Generic PR Feature / Fix")

        # 1. Try LLM analysis
        system_prompt = (
            "You are a Product Owner and Lead QA Architect reviewing PR diffs against acceptance criteria. "
            "Verify if code aligns with the intended story, does not introduce unrelated scope creep, "
            "and has sufficient automated test coverage. "
            "Return JSON matching: {\"score\": int (0-100), \"passed\": bool, \"feedback\": str, "
            "\"critical_issues\": [str], \"suggestions\": [str]}"
        )
        user_prompt = (
            f"User Story / PR Description:\n{story_desc}\n\n"
            f"PR Diff:\n{diff}\n\n"
            f"QA / Test Runner Report:\n{qa_payload}\n\n"
            "Analyze requirement match and return JSON."
        )

        llm_response = await self.call_llm(system_prompt, user_prompt)
        if llm_response and "score" in llm_response and "feedback" in llm_response:
            return AgentEvaluation(
                agent_name=self.name,
                score=int(llm_response["score"]),
                passed=bool(llm_response.get("passed", llm_response["score"] >= 75)),
                feedback=str(llm_response["feedback"]),
                critical_issues=list(llm_response.get("critical_issues", [])),
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # 2. Rule-based Heuristics
        return self._heuristic_analysis(diff_meta, qa_payload, story_desc)

    def _heuristic_analysis(
        self, diff_meta: Dict[str, Any], qa_payload: Dict[str, Any], story_desc: str
    ) -> AgentEvaluation:
        issues: List[str] = []
        suggestions: List[str] = []
        score = 90

        # Check QA test report if provided
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

        # Check if diff modified code without any test additions or changes
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
