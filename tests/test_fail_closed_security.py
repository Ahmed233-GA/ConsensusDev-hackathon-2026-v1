import pytest
from ai_engine.agents.consensus_engine import ConsensusEngine
from ai_engine.schemas import AgentEvaluation


def test_scanner_offline_fails_closed():
    """
    CRITICAL RULE 2: Scanner unavailable must NEVER become PASS.
    Must block auto-merge.
    """
    engine = ConsensusEngine(score_threshold=80)

    clean_evals = {
        "security": AgentEvaluation(agent_name="security", score=95, passed=True, feedback="Looks clean"),
        "tech_debt": AgentEvaluation(agent_name="tech_debt", score=90, passed=True, feedback="Clean"),
        "story_match": AgentEvaluation(agent_name="story_match", score=90, passed=True, feedback="Clean"),
        "performance": AgentEvaluation(agent_name="performance", score=90, passed=True, feedback="Clean"),
    }

    # Security scanner is offline / UNKNOWN
    res = engine.evaluate_consensus(
        evaluations=clean_evals,
        pr_number=101,
        security_context={"status": "UNKNOWN", "available": False, "error": "Connection refused"},
        qa_context={"status": "PASS", "available": True, "tests_passed": 10, "tests_failed": 0, "coverage_percentage": 90.0, "mutation_score": 85.0},
    )

    assert res.consensus is False
    assert "blocked" in res.summary.lower()
    assert "SECURITY_EVIDENCE_UNAVAILABLE" in res.details["blocking_reasons"]


def test_qa_offline_fails_closed():
    """
    CRITICAL RULE 2: QA unavailable must NEVER become PASS with fake 95% coverage.
    Must block auto-merge.
    """
    engine = ConsensusEngine(score_threshold=80)

    clean_evals = {
        "security": AgentEvaluation(agent_name="security", score=95, passed=True, feedback="Clean"),
        "tech_debt": AgentEvaluation(agent_name="tech_debt", score=90, passed=True, feedback="Clean"),
        "story_match": AgentEvaluation(agent_name="story_match", score=90, passed=True, feedback="Clean"),
        "performance": AgentEvaluation(agent_name="performance", score=90, passed=True, feedback="Clean"),
    }

    # QA Runner is offline / UNKNOWN
    res = engine.evaluate_consensus(
        evaluations=clean_evals,
        pr_number=102,
        security_context={"status": "PASS", "available": True, "vulnerabilities_count": 0, "critical_issues": []},
        qa_context={"status": "UNKNOWN", "available": False, "error": "QA Service unavailable"},
    )

    assert res.consensus is False
    assert "blocked" in res.summary.lower()
    assert "QA_EVIDENCE_UNAVAILABLE" in res.details["blocking_reasons"]


def test_critical_vulnerability_overrides_high_ai_score():
    """
    Even if AI agents rate the code highly, a detected critical vulnerability MUST block merge.
    """
    engine = ConsensusEngine(score_threshold=80)

    evals = {
        "security": AgentEvaluation(agent_name="security", score=30, passed=False, feedback="SQL Injection detected", critical_issues=["SQL Injection in db.py"]),
        "tech_debt": AgentEvaluation(agent_name="tech_debt", score=95, passed=True, feedback="Clean PEP8"),
        "story_match": AgentEvaluation(agent_name="story_match", score=95, passed=True, feedback="Matches story"),
        "performance": AgentEvaluation(agent_name="performance", score=95, passed=True, feedback="Fast"),
    }

    res = engine.evaluate_consensus(
        evaluations=evals,
        pr_number=103,
        security_context={"status": "FAIL", "available": True, "vulnerabilities_count": 1, "critical_issues": ["SQL Injection detected"]},
        qa_context={"status": "PASS", "available": True, "tests_passed": 5, "tests_failed": 0, "coverage_percentage": 90.0, "mutation_score": 85.0},
    )

    assert res.consensus is False
    assert "CRITICAL_VULNERABILITY" in res.details["blocking_reasons"]
    assert "blocked" in res.summary.lower()


def test_hardcoded_secret_fails_closed():
    """
    Detection of hardcoded secrets must trigger critical veto.
    """
    engine = ConsensusEngine(score_threshold=80)

    evals = {
        "security": AgentEvaluation(agent_name="security", score=20, passed=False, feedback="Hardcoded credential token", critical_issues=["Exposed API secret"]),
        "tech_debt": AgentEvaluation(agent_name="tech_debt", score=90, passed=True, feedback="Clean"),
        "story_match": AgentEvaluation(agent_name="story_match", score=90, passed=True, feedback="Clean"),
        "performance": AgentEvaluation(agent_name="performance", score=90, passed=True, feedback="Clean"),
    }

    res = engine.evaluate_consensus(
        evaluations=evals,
        pr_number=104,
        security_context={"status": "FAIL", "available": True, "vulnerabilities_count": 1, "critical_issues": ["Hardcoded API key detected"]},
        qa_context={"status": "PASS", "available": True, "tests_passed": 5, "tests_failed": 0, "coverage_percentage": 90.0, "mutation_score": 85.0},
    )

    assert res.consensus is False
    assert "CRITICAL_VULNERABILITY" in res.details["blocking_reasons"]
