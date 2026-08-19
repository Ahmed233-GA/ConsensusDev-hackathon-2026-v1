import logging
import re
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class PerformanceAgent(BaseReviewAgent):
    """
    AI Performance Reviewer Agent.
    Executes via OpenRouter / Cloud LLM model to analyze computational complexity (Big-O),
    nested loop bottlenecks, N+1 query patterns, and memory allocation efficiency.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="performance", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)

        # System prompt for LLM Model
        system_prompt = (
            "You are a Principal Performance Engineer reviewing a Pull Request diff. "
            "Analyze algorithmic time and space complexity (Big-O), memory leaks, N+1 database queries, "
            "inefficient loops, blocking I/O, and latency overhead. "
            "You MUST respond ONLY with valid JSON in this exact structure:\n"
            "{\n"
            '  "score": <integer from 0 to 100>,\n'
            '  "passed": <boolean: true if performant (score >= 75), false if performance regressions exist>,\n'
            '  "feedback": "<concise summary of complexity and performance characteristics>",\n'
            '  "critical_issues": ["<performance bottleneck 1>"],\n'
            '  "suggestions": ["<optimization suggestion 1>"]\n'
            "}"
        )

        user_prompt = (
            f"PR Diff:\n```diff\n{diff}\n```\n\n"
            "Analyze performance, Big-O complexity, and resource usage. Return JSON."
        )

        # 1. Execute LLM Model Call via OpenRouter
        llm_response = await self.call_llm(system_prompt, user_prompt)
        if llm_response and "score" in llm_response:
            score = int(llm_response.get("score", 90))
            passed = bool(llm_response.get("passed", score >= 75))
            feedback = str(llm_response.get("feedback", "O(1)/O(N) time complexity, minimal memory overhead"))

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

        nested_loop_pattern = re.compile(r"for\s+.*\s+in\s+.*:\s*\n\s+for\s+.*\s+in\s+.*:")
        sleep_in_code_pattern = re.compile(r"\btime\.sleep\s*\(\s*([1-9]\d*)\s*\)")
        db_in_loop_pattern = re.compile(r"(select\s+|find_one|\.query|\.filter)\(", re.IGNORECASE)

        added_code_block = "\n".join([line for _, line in diff_meta["added_lines"]])

        if nested_loop_pattern.search(added_code_block):
            issues.append("Nested loop detected (potential O(N^2) complexity)")
            score -= 20
            suggestions.append("Consider using lookup tables, sets, or batching to reduce O(N^2) complexity to O(N).")

        if sleep_in_code_pattern.search(added_code_block):
            issues.append("Hardcoded blocking time.sleep() detected")
            score -= 15
            suggestions.append("Use async event loops or non-blocking event-driven callbacks instead of blocking sleep.")

        lines = [line.strip() for _, line in diff_meta["added_lines"]]
        in_loop = False
        for line in lines:
            if line.startswith("for ") or line.startswith("while "):
                in_loop = True
            elif line.startswith("def ") or line.startswith("class "):
                in_loop = False
            elif in_loop and db_in_loop_pattern.search(line):
                issues.append("Potential N+1 database query pattern in loop")
                score -= 25
                suggestions.append("Batch database queries outside the loop using 'IN (...)' or prefetch relations.")
                break

        score = max(0, min(100, score))
        passed = score >= 75

        if passed and not issues:
            feedback = "O(1)/O(N) time complexity, minimal memory overhead"
        elif issues:
            feedback = f"Performance bottlenecks detected: {'; '.join(issues)}"
        else:
            feedback = "Acceptable performance characteristics"

        return AgentEvaluation(
            agent_name=self.name,
            score=score,
            passed=passed,
            feedback=feedback,
            critical_issues=issues,
            suggestions=suggestions,
        )
