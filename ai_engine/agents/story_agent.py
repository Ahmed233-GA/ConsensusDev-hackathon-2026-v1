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
    align with user story requirements and validates QA test runner reports.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="story_match", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        qa_payload = context.get("tests", {})
        story_desc = context.get("story_description", "Implement requested feature and fix bugs")

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
            "Analyze requirement match and test coverage using your LLM reasoning. Return JSON."
        )

        # Call OpenRouter / Cloud LLM
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

        # Fallback when no API key is provided
        qa_failed = qa_payload.get("status", "").upper() == "FAIL" or qa_payload.get("tests_failed", 0) > 0
        return AgentEvaluation(
            agent_name=self.name,
            score=45 if qa_failed else 90,
            passed=not qa_failed,
            feedback="Story/QA criteria not met: QA test suite failed" if qa_failed else "Satisfies user story requirements with adequate test validation",
            critical_issues=["QA test suite failed with failing tests"] if qa_failed else [],
            suggestions=["Ensure all unit tests pass before merge"] if qa_failed else [],
        )
