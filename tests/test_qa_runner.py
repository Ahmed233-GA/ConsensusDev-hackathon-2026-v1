import pytest
from fastapi.testclient import TestClient
from qa_runner.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_tests_valid_diff():
    payload = {"diff": "some code diff"}
    response = client.post("/run-tests", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    # Ensure both keys are present
    assert "test_results" in json_data
    assert "coverage_percentage" in json_data
    assert "mutation_score" in json_data
    assert isinstance(json_data["mutation_score"], (int, float))
    # Basic structure checks
    assert isinstance(json_data["coverage_percentage"], (int, float))
    assert isinstance(json_data["test_results"], dict)


def test_run_tests_empty_diff():
    payload = {"diff": "   "}
    response = client.post("/run-tests", json=payload)
    assert response.status_code == 400
    assert "detail" in response.json()
