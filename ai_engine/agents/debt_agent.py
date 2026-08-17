import logging
import re
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class TechDebtAgent(BaseReviewAgent):
    """
    AI Tech Debt Reviewer Agent.
    Analyzes code cleanliness, PEP8 / formatting compliance, code smells,
    bare exceptions, leftover debug print statements, and architectural maintainability.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="tech_debt", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)

        # 1. Try LLM analysis
        system_prompt = (
            "You are a Staff Software Engineer and Code Quality Architect reviewing a PR. "
            "Evaluate code maintainability, PEP8/clean code compliance, presence of code smells, "
            "cyclomatic complexity, bare exceptions, and debug artifacts. "
            "Return JSON matching: {\"score\": int (0-100), \"passed\": bool, \"feedback\": str, "
            "\"critical_issues\": [str], \"suggestions\": [str]}"
        )
        user_prompt = f"PR Diff:\n{diff}\n\nAnalyze technical debt and code quality."

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

            # Bare except
            if bare_except_pattern.search(stripped):
                issues.append(f"Bare except clause in {filename}")
                score -= 15
                suggestions.append("Catch specific exceptions (e.g. `except ValueError:`) instead of catching all exceptions.")

            # Leftover debug print statements in non-script files
            if print_statement_pattern.search(line) and not filename.endswith("_test.py") and not filename.startswith("test_"):
                issues.append(f"Leftover `print` statement in {filename}")
                score -= 10
                suggestions.append("Replace raw `print()` statements with structured logging (`logger.info` or `logger.debug`).")

            # TODO / FIXME tags
            if todo_fixme_pattern.search(stripped):
                suggestions.append(f"Unresolved TODO/FIXME comment found in {filename}")
                score -= 5

            # Wildcard imports
            if wildcard_import_pattern.search(stripped):
                issues.append(f"Wildcard import (`from ... import *`) in {filename}")
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
