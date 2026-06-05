import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.workers.runner import WorkerRunner  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def run_worker_once() -> None:
    item = WorkerRunner(worker_id="test-worker").run_once()
    assert item is not None
    assert item.status == "succeeded"


def complete_ingestion_upload(client: TestClient, upload_response, *, headers: dict | None = None) -> dict:
    assert upload_response.status_code == 202
    accepted = upload_response.json()
    run_worker_once()
    job_response = client.get(f"/api/v1/ingestion/jobs/{accepted['job_id']}", headers=headers)
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    quality_response = client.get(f"/api/v1/datasets/{job['dataset_id']}/quality", headers=headers)
    assert quality_response.status_code == 200
    quality = quality_response.json()
    return {
        **accepted,
        "dataset_id": job["dataset_id"],
        "status": job["status"],
        "current_step": job["current_step"],
        "progress_percent": job["progress_percent"],
        "quality_score": job["quality_score"],
        "row_count": job["row_count"],
        "rejected_rows": job["rejected_rows"],
        "storage_path": job["storage_path"],
        "report_id": quality["id"],
        "finished_at": job["finished_at"],
    }


@pytest.fixture()
def complete_upload(client: TestClient):
    def _complete(upload_response, *, headers: dict | None = None) -> dict:
        return complete_ingestion_upload(client, upload_response, headers=headers)

    return _complete


@pytest.fixture()
def run_worker():
    return run_worker_once
