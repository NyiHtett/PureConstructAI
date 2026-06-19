from __future__ import annotations

from app.db.repositories import LocalJsonRepository
from app.schemas import JobStatus


def test_local_repository_stores_annotation_job_with_assets(tmp_path) -> None:
    repository = LocalJsonRepository(tmp_path / "metadata")

    image = repository.create_image_asset(
        {
            "_id": "image-1",
            "project_id": "project-1",
            "wall_id": "wall-1",
            "original_filename": "wall.jpg",
            "width": 640,
            "height": 480,
            "content_type": "image/jpeg",
            "storage_backend": "local",
            "local_path": "/tmp/wall.jpg",
        }
    )
    repository.create_annotation_job(
        {
            "_id": "job-1",
            "image_asset_id": image["_id"],
            "calibration_payload_id": None,
            "annotation_mode": "electrical_lines",
            "model_provider": "mock",
            "status": JobStatus.rendered.value,
            "warnings": [],
        }
    )
    repository.save_rendered_asset(
        {
            "_id": "rendered-1",
            "annotation_job_id": "job-1",
            "content_type": "image/jpeg",
            "storage_backend": "local",
            "local_path": "/tmp/rendered.jpg",
        }
    )

    result = repository.get_annotation_job_with_assets("job-1")

    assert result is not None
    assert result["job"]["status"] == JobStatus.rendered.value
    assert result["rendered_assets"][0]["local_path"] == "/tmp/rendered.jpg"


def test_local_repository_updates_review_status(tmp_path) -> None:
    repository = LocalJsonRepository(tmp_path / "metadata")
    repository.create_annotation_job(
        {
            "_id": "job-1",
            "image_asset_id": "image-1",
            "calibration_payload_id": None,
            "annotation_mode": "field_notes",
            "model_provider": "mock",
            "status": JobStatus.rendered.value,
            "warnings": [],
        }
    )

    repository.add_review_event(
        {
            "annotation_job_id": "job-1",
            "reviewer_id": "reviewer-1",
            "event_type": "approved",
            "notes": "ok",
        }
    )
    repository.update_annotation_job_status("job-1", JobStatus.approved_for_field_reference)

    result = repository.get_annotation_job_with_assets("job-1")

    assert result["job"]["status"] == JobStatus.approved_for_field_reference.value
    assert result["review_events"][0]["event_type"] == "approved"
