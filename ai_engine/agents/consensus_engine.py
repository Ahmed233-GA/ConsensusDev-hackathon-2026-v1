import logging
from typing import Any, Dict, List, Optional

from ai_engine.schemas import AgentEvaluation, AnalyzePRResponse

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Consensus Decision Engine for ConsensusDev.
    Aggregates the evaluations of all 4 AI agents, applies strict security/QA veto gates,
    computes weighted scores, and produces final decision + executive summary.
    """

    def __init__(self, score_threshold: int = 80):
        self.score_threshold = score_threshold
        # Weights for scoring
        self.weights = {
            "security": 2.0,
            "tech_debt": 1.0,
            "story_match": 1.0,
            "performance": 1.0,
        }

    def evaluate_consensus(
        self,
        evaluations: Dict[str, AgentEvaluation],
        pr_number: Optional[int] = None,
        security_context: Optional[Dict[str, Any]] = None,
        qa_context: Optional[Dict[str, Any]] = None,
    ) -> AnalyzePRResponse:
        security_context = security_context or {}
        qa_context = qa_context or {}

        total_weight = 0.0
        weighted_sum = 0.0
        blockers: List[str] = []
        feedback_map: Dict[str, str] = {}
        agent_details: Dict[str, Any] = {}

        for agent_key, eval_result in evaluations.items():
            weight = self.weights.get(agent_key, 1.0)
            weighted_sum += eval_result.score * weight
            total_weight += weight
            feedback_map[agent_key] = eval_result.feedback
            agent_details[agent_key] = {
                "score": eval_result.score,
                "passed": eval_result.passed,
                "critical_issues": eval_result.critical_issues,
                "suggestions": eval_result.suggestions,
            }

            # Collect blockers from agents
            if not eval_result.passed and eval_result.critical_issues:
                for issue in eval_result.critical_issues:
                    blockers.append(f"[{agent_key.upper()}] {issue}")

        # Compute overall normalized score (0-100)
        overall_score = int(round(weighted_sum / total_weight)) if total_weight > 0 else 0
        overall_score = max(0, min(100, overall_score))

        # Check external scanner & QA contexts
        if security_context.get("status", "").upper() == "FAIL":
            for issue in security_context.get("critical_issues", []):
                blockers.append(f"[SCANNER] {issue}")

        if qa_context.get("status", "").upper() == "FAIL" or qa_context.get("tests_failed", 0) > 0:
            blockers.append(f"[QA] Test suite failed with {qa_context.get('tests_failed', 1)} failures")

        # Consensus Gate Decision:
        # 1. Must have 0 critical blockers
        # 2. Security agent must pass
        # 3. Overall score must be >= score_threshold
        security_passed = evaluations.get("security", AgentEvaluation(agent_name="security", score=0, passed=False, feedback="")).passed
        consensus_approved = (len(blockers) == 0) and security_passed and (overall_score >= self.score_threshold)

        pr_label = f"PR #{pr_number}" if pr_number else "PR"

        if consensus_approved:
            summary = f"{pr_label} meets all quality and security criteria. Approved for auto-merge."
        else:
            blocker_text = "; ".join(blockers[:3]) if blockers else f"Score {overall_score} below threshold {self.score_threshold}"
            summary = f"{pr_label} failed consensus review: {blocker_text}. Auto-merge blocked."

        return AnalyzePRResponse(
            consensus=consensus_approved,
            score=overall_score,
            agents_feedback=feedback_map,
            summary=summary,
            details=agent_details,
        )
