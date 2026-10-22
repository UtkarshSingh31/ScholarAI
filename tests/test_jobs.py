from unittest.mock import patch

from app import jobs


def test_submit_job_exposes_queued_job(monkeypatch):
    class FakeExecutor:
        def submit(self, function, *args):
            return None

    monkeypatch.setattr(jobs, "_executor", FakeExecutor())
    job_id = jobs.submit_job({"agent_status": {"profile_intelligence": "pending"}})

    job = jobs.get_job(job_id)
    assert job is not None
    assert job["job_id"] == job_id
    assert job["status"] == "queued"
