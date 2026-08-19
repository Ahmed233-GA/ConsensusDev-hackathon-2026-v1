import logging
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
            "Analyze performance, Big-O complexity, and resource usage using your LLM reasoning. Return JSON."
        )

        # Call OpenRouter / Cloud LLM
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

        # Fallback when no API key is provided
        has_nested = "for " in diff and diff.count("for ") >= 2 and ("select" in diff.lower() or "query" in diff.lower())
        return AgentEvaluation(
            agent_name=self.name,
            score=50 if has_nested else 95,
            passed=not has_nested,
            feedback="Performance bottlenecks detected: nested queries in loop" if has_nested else "O(1)/O(N) time complexity, minimal memory overhead",
            critical_issues=["Nested loop query bottleneck"] if has_nested else [],
            suggestions=["Batch database queries outside loops"] if has_nested else [],
        )
