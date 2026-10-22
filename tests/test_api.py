from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_is_served():
    response = client.get("/")

    assert response.status_code == 200
    assert "ScholarAI Dashboard" in response.text


def test_workflow_rejects_invalid_profile_json():
    response = client.post(
        "/workflow",
        data={"profile": "{not-json", "profile_urls": "[]"},
    )

    assert response.status_code == 400
    assert "valid JSON" in response.json()["detail"]


def test_workflow_job_rejects_unknown_job():
    response = client.get("/workflow/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow job not found."
