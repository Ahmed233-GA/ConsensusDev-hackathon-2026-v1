import logging
import re
from typing import Any, Dict, List

from ai_engine.agents.base_agent import BaseReviewAgent
from ai_engine.schemas import AgentEvaluation

logger = logging.getLogger(__name__)


class PerformanceAgent(BaseReviewAgent):
    """
    AI Performance Reviewer Agent.
    Analyzes computational complexity (Big-O), nested iteration bottlenecks,
    N+1 query patterns, blocking synchronous calls, and memory allocation overhead.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__(name="performance", weight=weight)

    async def evaluate(self, diff: str, context: Dict[str, Any]) -> AgentEvaluation:
        diff_meta = self.extract_diff_metadata(diff)

        # 1. Try LLM analysis
        system_prompt = (
            "You are a Principal Performance Engineer reviewing a Pull Request diff. "
            "Analyze algorithmic time and space complexity (Big-O), memory leaks, N+1 query patterns, "
            "inefficient loops, and blocking I/O calls. "
            "Return JSON matching: {\"score\": int (0-100), \"passed\": bool, \"feedback\": str, "
            "\"critical_issues\": [str], \"suggestions\": [str]}"
        )
        user_prompt = f"PR Diff:\n{diff}\n\nAnalyze performance implications."

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

        # Heuristic detection patterns
        nested_loop_pattern = re.compile(r"for\s+.*\s+in\s+.*:\s*\n\s+for\s+.*\s+in\s+.*:")
        sleep_in_code_pattern = re.compile(r"\btime\.sleep\s*\(\s*([1-9]\d*)\s*\)")
        db_in_loop_pattern = re.compile(r"(select\s+|find_one|\.query|\.filter)\(", re.IGNORECASE)

        added_code_block = "\n".join([line for _, line in diff_meta["added_lines"]])

        # Check for nested loops
        if nested_loop_pattern.search(added_code_block):
            issues.append("Nested loop detected (potential O(N^2) complexity)")
            score -= 20
            suggestions.append("Consider using lookup tables, sets, or batching to reduce O(N^2) complexity to O(N).")

        # Check for arbitrary long sleeps
        if sleep_in_code_pattern.search(added_code_block):
            issues.append("Hardcoded blocking time.sleep() detected")
            score -= 15
            suggestions.append("Use async event loops or non-blocking event-driven callbacks instead of blocking sleep.")

        # Check for DB calls in loops
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
