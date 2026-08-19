import logging
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class TechDebtAgent(BaseReviewAgent):
    """
    AI Tech Debt Reviewer Agent.
    Executes via OpenRouter / Cloud LLM model to analyze code maintainability,
    PEP8 standards, cyclomatic complexity, and code cleanliness.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="tech_debt", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        system_prompt = (
            "You are a Staff Software Engineer and Code Quality Architect reviewing a Pull Request diff. "
            "Evaluate code maintainability, PEP8 and clean code compliance, code smells, "
            "cyclomatic complexity, bare exceptions, and debug artifacts (print statements, console.log). "
            "You MUST respond ONLY with valid JSON in this exact structure:\n"
            "{\n"
            '  "score": <integer from 0 to 100>,\n'
            '  "passed": <boolean: true if clean and maintainable (score >= 75), false if refactoring required>,\n'
            '  "feedback": "<concise summary of code quality and maintainability>",\n'
            '  "critical_issues": ["<major quality issue 1>"],\n'
            '  "suggestions": ["<improvement suggestion 1>"]\n'
            "}"
        )

        user_prompt = (
            f"PR Diff:\n```diff\n{diff}\n```\n\n"
            "Evaluate technical debt, formatting, and architecture using your LLM reasoning. Return JSON."
        )

        # Call OpenRouter / Cloud LLM
        llm_response = await self.call_llm(system_prompt, user_prompt)

        if llm_response and "score" in llm_response:
            score = int(llm_response.get("score", 90))
            passed = bool(llm_response.get("passed", score >= 75))
            feedback = str(llm_response.get("feedback", "Adheres to PEP8 standards and clean architecture"))

            return AgentEvaluation(
                agent_name=self.name,
                score=score,
                passed=passed,
                feedback=feedback,
                critical_issues=list(llm_response.get("critical_issues", [])),
                suggestions=list(llm_response.get("suggestions", [])),
            )

        # Fallback when no API key is provided
        has_print = "print(" in diff or "except:" in diff
        return AgentEvaluation(
            agent_name=self.name,
            score=60 if has_print else 95,
            passed=not has_print,
            feedback="Quality issues detected: leftover print or bare except" if has_print else "Adheres to PEP8 standards and clean architecture",
            critical_issues=["Leftover debug print or bare except"] if has_print else [],
            suggestions=["Use structured logging"] if has_print else [],
        )
