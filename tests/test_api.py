"""
Tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "RepoDoctor AI"


def test_scan_api_endpoint():
    response = client.post("/api/scan", json={"target": "examples/buggy_ml_repo"})
    assert response.status_code == 200
    data = response.json()
    assert "scorecard" in data
    assert "issues" in data
    assert len(data["issues"]) > 0


def test_repair_api_endpoint():
    response = client.post("/api/repair", json={"target": "examples/buggy_ml_repo"})
    assert response.status_code == 200
    data = response.json()
    assert "patches" in data
    assert "validation_results" in data


def test_report_api_endpoint():
    response = client.post("/api/report", json={"target": "examples/buggy_ml_repo"})
    assert response.status_code == 200
    assert "markdown" in response.json()
