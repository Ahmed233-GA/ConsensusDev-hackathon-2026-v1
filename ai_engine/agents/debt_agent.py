import logging
import re
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
        diff_meta = self.extract_diff_metadata(diff)

        # System prompt for LLM Model
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
            "Evaluate technical debt, formatting, and architecture. Return JSON."
        )

        # 1. Execute LLM Model Call via OpenRouter
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

        # 2. Fallback when running offline without API keys
        return self._heuristic_analysis(diff_meta)

    def _heuristic_analysis(self, diff_meta: Dict[str, Any]) -> AgentEvaluation:
        issues: List[str] = []
        suggestions: List[str] = []
        score = 95

        bare_except_pattern = re.compile(r"except\s*:\s*$", re.IGNORECASE)
        print_statement_pattern = re.compile(r"^\s*print\s*\(", re.IGNORECASE)
        todo_fixme_pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
        wildcard_import_pattern = re.compile(r"from\s+[\w\.]+\s+import\s+\*", re.IGNORECASE)

        for filename, line in diff_meta["added_lines"]:
            stripped = line.strip()
            if bare_except_pattern.search(stripped):
                issues.append(f"Bare except clause in {filename}")
                score -= 15
                suggestions.append("Catch specific exceptions (e.g. `except ValueError:`) instead of catching all exceptions.")
            if print_statement_pattern.search(line) and not filename.endswith("_test.py") and not filename.startswith("test_"):
                issues.append(f"Leftover `print` statement in {filename}")
                score -= 10
                suggestions.append("Replace raw `print()` statements with structured logging.")
            if todo_fixme_pattern.search(stripped):
                suggestions.append(f"Unresolved TODO/FIXME comment found in {filename}")
                score -= 5
            if wildcard_import_pattern.search(stripped):
                issues.append(f"Wildcard import in {filename}")
                score -= 10
                suggestions.append("Explicitly import required classes/functions instead of using `*`.")

        score = max(0, min(100, score))
        passed = score >= 75
        if passed and not issues:
            feedback = "Adheres to PEP8 standards and clean architecture"
        elif issues:
            feedback = f"Quality issues detected: {', '.join(issues[:2])}"
        else:
            feedback = "Acceptable code quality with minor suggestions"

        return AgentEvaluation(
            agent_name=self.name,
            score=score,
            passed=passed,
            feedback=feedback,
            critical_issues=issues,
            suggestions=suggestions,
        )
