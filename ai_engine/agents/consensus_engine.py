import logging
import os
from typing import Any, Dict, List, Optional

from ai_engine.schemas import AgentEvaluation, AnalyzePRResponse

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Consensus Decision Engine for ConsensusDev.
    Aggregates the evaluations of all 4 AI agents, applies strict fail-closed
    security and QA veto gates, computes weighted scores, and produces final decision.
    """

    def __init__(self, score_threshold: Optional[int] = None):
        env_threshold = os.getenv("CONSENSUS_MIN_SCORE")
        self.score_threshold = int(env_threshold) if env_threshold else (score_threshold or 80)
        self.min_coverage = float(os.getenv("MIN_COVERAGE_PERCENTAGE", "80.0"))
        self.min_mutation = float(os.getenv("MIN_MUTATION_SCORE", "70.0"))

        # Canonical weights: Security (40%), Tech Debt (20%), Story Match (20%), Performance (20%)
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
        blocking_reasons: List[str] = []
        feedback_map: Dict[str, str] = {}
        agent_details: Dict[str, Any] = {}

        # 1. AI Agents Evaluation Aggregation
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

            if not eval_result.passed and eval_result.critical_issues:
                for issue in eval_result.critical_issues:
                    blockers.append(f"[{agent_key.upper()}] {issue}")
                    if agent_key == "security":
                        blocking_reasons.append("CRITICAL_SECURITY_ISSUE")
                    elif agent_key == "story_match":
                        blocking_reasons.append("STORY_REQUIREMENTS_NOT_MET")

        overall_score = int(round(weighted_sum / total_weight)) if total_weight > 0 else 0
        overall_score = max(0, min(100, overall_score))

        # 2. Strict Fail-Closed Security Evidence Gate
        sec_status = security_context.get("status", "UNKNOWN").upper()
        if sec_status != "PASS":
            if sec_status in ["UNKNOWN", "ERROR", "TIMEOUT", "OFFLINE"]:
                blockers.append(f"[SECURITY GATE] Security evidence unavailable ({sec_status})")
                blocking_reasons.append("SECURITY_EVIDENCE_UNAVAILABLE")
            else:
                for issue in security_context.get("critical_issues", []):
                    blockers.append(f"[SCANNER] {issue}")
                blocking_reasons.append("CRITICAL_VULNERABILITY")
        elif security_context.get("vulnerabilities_count", 0) > 0 or len(security_context.get("critical_issues", [])) > 0:
            for issue in security_context.get("critical_issues", []):
                blockers.append(f"[SCANNER] {issue}")
            blocking_reasons.append("CRITICAL_VULNERABILITY")

        # 3. Strict Fail-Closed QA Evidence Gate
        qa_status = qa_context.get("status", "UNKNOWN").upper()
        if qa_status != "PASS":
            if qa_status in ["UNKNOWN", "ERROR", "TIMEOUT", "OFFLINE"]:
                blockers.append(f"[QA GATE] QA test evidence unavailable ({qa_status})")
                blocking_reasons.append("QA_EVIDENCE_UNAVAILABLE")
            else:
                failed_tests = qa_context.get("tests_failed", 1)
                blockers.append(f"[QA] Test suite failed with {failed_tests} test failures")
                blocking_reasons.append("TEST_FAILURE")
        else:
            if qa_context.get("tests_failed", 0) > 0:
                blockers.append(f"[QA] Test suite has {qa_context.get('tests_failed')} failing tests")
                blocking_reasons.append("TEST_FAILURE")
            
            cov = qa_context.get("coverage_percentage")
            if cov is not None and cov < self.min_coverage:
                blockers.append(f"[QA] Test coverage ({cov:.1f}%) is below minimum required ({self.min_coverage:.1f}%)")
                blocking_reasons.append("COVERAGE_BELOW_THRESHOLD")

            mut = qa_context.get("mutation_score")
            if mut is not None and mut < self.min_mutation:
                blockers.append(f"[QA] Mutation score ({mut:.1f}%) is below minimum required ({self.min_mutation:.1f}%)")
                blocking_reasons.append("MUTATION_BELOW_THRESHOLD")

        # 4. Score Threshold & Final Gate Decision
        security_eval = evaluations.get("security")
        if security_eval and not security_eval.passed and security_eval.critical_issues:
            blocking_reasons.append("SECURITY_AGENT_REJECTED")

        if overall_score < self.score_threshold and not any("EVIDENCE_UNAVAILABLE" in r for r in blocking_reasons):
            blocking_reasons.append("SCORE_BELOW_THRESHOLD")

        consensus_approved = (
            (len(blockers) == 0)
            and (security_eval is not None and security_eval.passed)
            and (overall_score >= self.score_threshold)
            and (sec_status == "PASS")
            and (qa_status == "PASS")
        )

        pr_label = f"PR #{pr_number}" if pr_number else "PR"

        if consensus_approved:
            summary = f"{pr_label} meets all quality and security criteria (Score: {overall_score}/100). Approved for auto-merge."
        else:
            blocker_text = "; ".join(blockers[:3]) if blockers else f"Consensus score {overall_score} below threshold {self.score_threshold}"
            summary = f"{pr_label} failed consensus review: {blocker_text}. Auto-merge blocked."

        # Unique blocking reasons
        unique_reasons = list(dict.fromkeys(blocking_reasons))

        sec_gate_status = "passed" if (sec_status == "PASS" and (security_eval is None or security_eval.passed)) else ("unknown" if sec_status in ["UNKNOWN", "ERROR", "TIMEOUT", "OFFLINE"] else "failed")
        qa_gate_status = "passed" if (qa_status == "PASS" and qa_context.get("tests_failed", 0) == 0) else ("unknown" if qa_status in ["UNKNOWN", "ERROR", "TIMEOUT", "OFFLINE"] else "failed")
        evidence_gate_status = "verified" if (sec_status == "PASS" and qa_status == "PASS") else "incomplete"

        return AnalyzePRResponse(
            consensus=consensus_approved,
            score=overall_score,
            agents_feedback=feedback_map,
            summary=summary,
            details={
                **agent_details,
                "blocking_reasons": unique_reasons,
                "gates": {
                    "security": sec_gate_status,
                    "qa": qa_gate_status,
                    "evidence": evidence_gate_status,
                },
            },
        )
