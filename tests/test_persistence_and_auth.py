import pytest
from fastapi.testclient import TestClient
from gateway.main import app
from gateway.auth import hash_password, verify_password, create_access_token, decode_access_token
from gateway.database import (
    init_db,
    save_review_record,
    get_all_reviews_from_db,
    get_review_by_id_from_db,
    save_audit_log_to_db,
    get_audit_logs_from_db,
    get_dashboard_stats_from_db,
    SessionLocal,
)
from gateway.seed_admin import seed_admin_user
from gateway.models.db import User


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    seed_admin_user()


def test_password_hashing():
    pwd = "superSecretPassword123"
    hashed = hash_password(pwd)

    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongPassword", hashed) is False


def test_jwt_token_flow():
    payload = {"sub": "admin", "user_id": 1, "role": "admin"}
    token = create_access_token(payload)

    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"

    # Invalid token test
    assert decode_access_token("invalid.token.here") is None


def test_seed_admin_user():
    admin = seed_admin_user()
    assert admin is not None
    assert admin.username == "admin"
    assert admin.is_active is True

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        assert user is not None
        assert user.role == "admin"
    finally:
        db.close()


def test_review_persistence_and_retrieval():
    sample_review = {
        "meta": {
            "id": "pr-999",
            "prNumber": 999,
            "title": "feat: persistence test PR",
            "author": {"name": "TestDev", "username": "TestDev"},
            "commitHash": "99999999999999999999999999999999",
            "shortHash": "9999999",
            "sourceBranch": "feature/persistence",
            "targetBranch": "main",
            "repo": "ConsensusDev/test",
            "createdAt": "2026-08-21T00:00:00Z",
            "updatedAt": "2026-08-21T00:00:00Z",
        },
        "consensus": {
            "score": 92,
            "decision": "approved",
            "gates": {"security": "passed", "qa": "passed", "evidence": "verified"},
            "summary": "PR #999 meets all criteria",
            "blocking_reasons": [],
        },
        "agents": [],
        "findings": [
            {
                "id": "find-test-1",
                "severity": "medium",
                "tool": "Scanner",
                "ruleId": "TEST_RULE_1",
                "engine": "fallback_regex_ast",
                "file": "calc.py",
                "line": 5,
                "description": "Test finding",
            }
        ],
        "qaStats": {
            "status": "PASS",
            "testsPassed": 10,
            "testsFailed": 0,
            "coveragePercentage": 95.0,
            "mutationScore": 88.0,
            "suites": [],
        },
        "merged": False,
        "reviewTimeSeconds": 1.25,
        "status": "APPROVED",
    }

    record = save_review_record(sample_review)
    assert record.id == "pr-999"
    assert record.pr_number == 999
    assert record.score == 92
    assert record.consensus_decision == "approved"

    # Query from DB
    retrieved = get_review_by_id_from_db("pr-999")
    assert retrieved is not None
    assert retrieved["meta"]["id"] == "pr-999"
    assert retrieved["consensus"]["score"] == 92
    assert len(retrieved["findings"]) == 1
    assert retrieved["findings"][0]["ruleId"] == "TEST_RULE_1"

    all_reviews = get_all_reviews_from_db()
    assert any(r["meta"]["id"] == "pr-999" for r in all_reviews)


def test_audit_log_persistence():
    log_rec = save_audit_log_to_db(
        service="TestService",
        level="INFO",
        message="Persistence test audit message",
        event="TEST_EVENT",
        actor="tester",
        review_id="pr-999",
        metadata={"detail_key": "detail_val"},
    )
    assert log_rec.id.startswith("log-")
    assert log_rec.service == "TestService"

    logs = get_audit_logs_from_db(limit=10)
    assert any(l["message"] == "Persistence test audit message" for l in logs)


def test_dashboard_stats_query():
    stats = get_dashboard_stats_from_db()
    assert isinstance(stats, dict)
    assert "totalReviews" in stats
    assert "approvalRate" in stats
    assert "avgScore" in stats
    assert "activeAgents" in stats
    assert stats["totalReviews"] >= 1


def test_auth_login_api():
    client = TestClient(app)

    # 1. Success login
    res = client.post("/auth/login", json={"operator_id": "admin", "access_key": "admin1234"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "authenticated"
    assert "token" in data
    assert data["user"]["username"] == "admin"

    token = data["token"]

    # 2. Access /auth/me with Bearer token
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["username"] == "admin"

    # 3. Invalid credentials
    bad_res = client.post("/auth/login", json={"operator_id": "admin", "access_key": "wrongpass"})
    assert bad_res.status_code == 401

    # 4. Missing fields
    missing_res = client.post("/auth/login", json={"operator_id": ""})
    assert missing_res.status_code == 400

    # 5. Access /auth/me without token on a clean unauthenticated client
    clean_client = TestClient(app)
    unauth_res = clean_client.get("/auth/me")
    assert unauth_res.status_code == 401
