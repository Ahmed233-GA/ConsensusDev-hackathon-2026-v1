from ai_engine.agents.consensus_engine import ConsensusEngine
from ai_engine.schemas import AgentEvaluation


def test_consensus_engine_approves_clean_evaluations():
    engine = ConsensusEngine(score_threshold=80)

    evaluations = {
        "security": AgentEvaluation(
            agent_name="security",
            score=95,
            passed=True,
            feedback="Clean - no secrets or CVEs found",
        ),
        "tech_debt": AgentEvaluation(
            agent_name="tech_debt",
            score=90,
            passed=True,
            feedback="Adheres to PEP8 standards",
        ),
        "story_match": AgentEvaluation(
            agent_name="story_match",
            score=90,
            passed=True,
            feedback="Satisfies user story requirements",
        ),
        "performance": AgentEvaluation(
            agent_name="performance",
            score=92,
            passed=True,
            feedback="O(1) time complexity, minimal memory overhead",
        ),
    }

    response = engine.evaluate_consensus(
        evaluations=evaluations,
        pr_number=142,
        security_context={"status": "PASS", "vulnerabilities_count": 0},
        qa_context={"status": "PASS", "tests_passed": 12, "coverage_percentage": 95.0},
    )

    assert response.consensus is True
    assert response.score >= 90
    assert "PR #142 meets all quality and security criteria" in response.summary
    assert response.agents_feedback["security"] == "Clean - no secrets or CVEs found"


def test_consensus_engine_blocks_on_security_critical_issue():
    engine = ConsensusEngine(score_threshold=80)

    evaluations = {
        "security": AgentEvaluation(
            agent_name="security",
            score=40,
            passed=False,
            feedback="SQL Injection detected",
            critical_issues=["SQL Injection in app/db.py"],
        ),
        "tech_debt": AgentEvaluation(
            agent_name="tech_debt",
            score=90,
            passed=True,
            feedback="Adheres to PEP8 standards",
        ),
        "story_match": AgentEvaluation(
            agent_name="story_match",
            score=90,
            passed=True,
            feedback="Satisfies user story requirements",
        ),
        "performance": AgentEvaluation(
            agent_name="performance",
            score=90,
            passed=True,
            feedback="O(1) complexity",
        ),
    }

    response = engine.evaluate_consensus(
        evaluations=evaluations,
        pr_number=101,
        security_context={"status": "FAIL", "critical_issues": ["SQL Injection in app/db.py"]},
        qa_context={"status": "PASS"},
    )

    assert response.consensus is False
    assert "failed consensus review" in response.summary
    assert "Auto-merge blocked" in response.summary


def test_consensus_engine_blocks_on_qa_failures():
    engine = ConsensusEngine(score_threshold=80)

    evaluations = {
        "security": AgentEvaluation(
            agent_name="security",
            score=95,
            passed=True,
            feedback="Clean",
        ),
        "tech_debt": AgentEvaluation(
            agent_name="tech_debt",
            score=85,
            passed=True,
            feedback="Clean",
        ),
        "story_match": AgentEvaluation(
            agent_name="story_match",
            score=40,
            passed=False,
            feedback="Failing tests",
            critical_issues=["QA test suite failed with 3 failing tests"],
        ),
        "performance": AgentEvaluation(
            agent_name="performance",
            score=90,
            passed=True,
            feedback="Clean",
        ),
    }

    response = engine.evaluate_consensus(
        evaluations=evaluations,
        pr_number=102,
        security_context={"status": "PASS"},
        qa_context={"status": "FAIL", "tests_failed": 3},
    )

    assert response.consensus is False
    assert "failed consensus review" in response.summary
