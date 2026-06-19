from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

os.environ["MODEL_PROVIDER"] = "mock"
os.environ["PERSISTENCE_BACKEND"] = "local"
_storage_root = tempfile.TemporaryDirectory()
os.environ["LOCAL_STORAGE_ROOT"] = str(Path(_storage_root.name) / "storage")
os.environ["METADATA_STORAGE_ROOT"] = str(Path(_storage_root.name) / "metadata")

from app.main import app
from app.schemas import AnnotationMode


client = TestClient(app)


def _make_jpg_bytes() -> bytes:
    image = np.full((480, 720, 3), (185, 180, 172), dtype=np.uint8)
    cv2.rectangle(image, (55, 42), (665, 390), (203, 199, 190), -1)
    for x in range(110, 660, 95):
        cv2.line(image, (x, 58), (x, 376), (145, 140, 132), 2, cv2.LINE_AA)
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    return buffer.tobytes()


def _post_annotation(mode: AnnotationMode):
    return client.post(
        "/api/v1/annotations",
        data={
            "annotation_mode": mode.value,
            "project_id": "project-1",
            "wall_id": "wall-a",
            "notes": "test request",
        },
        files={"image": ("wall.jpg", _make_jpg_bytes(), "image/jpeg")},
    )


def test_upload_image_works() -> None:
    response = _post_annotation(AnnotationMode.electrical_lines)

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["annotation_mode"] == "electrical_lines"
    assert payload["annotated_image_url"].endswith("/image")
    assert payload["spec"]["outlet_boxes"]


def test_each_annotation_mode_returns_rendered_image_url() -> None:
    for mode in AnnotationMode:
        response = _post_annotation(mode)

        assert response.status_code == 200
        payload = response.json()
        assert payload["annotation_mode"] == mode.value
        assert payload["annotated_image_url"] == f"/api/v1/annotations/{payload['job_id']}/image"


def test_rendered_image_can_be_fetched() -> None:
    create_response = _post_annotation(AnnotationMode.field_notes)
    payload = create_response.json()

    image_response = client.get(payload["annotated_image_url"])

    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/jpeg"
    assert len(image_response.content) > 0


def test_low_confidence_request_still_renders_with_warning() -> None:
    response = client.post(
        "/api/v1/annotations",
        data={
            "annotation_mode": AnnotationMode.field_notes.value,
            "notes": "low confidence: blurry photo",
        },
        files={"image": ("wall.jpg", _make_jpg_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["annotated_image_url"]
    assert any("Low confidence" in warning for warning in payload["warnings"])


def test_review_endpoint_updates_status() -> None:
    create_response = _post_annotation(AnnotationMode.electrical_lines)
    job_id = create_response.json()["job_id"]

    review_response = client.post(
        f"/api/v1/annotations/{job_id}/review",
        json={
            "event_type": "approved",
            "reviewer_id": "reviewer-1",
            "notes": "usable as field reference",
        },
    )

    assert review_response.status_code == 200
    payload = review_response.json()
    assert payload["job_id"] == job_id
    assert payload["status"] == "approved_for_field_reference"


def test_approved_review_is_available_as_field_reference() -> None:
    create_response = _post_annotation(AnnotationMode.stud_locations)
    job_id = create_response.json()["job_id"]

    client.post(
        f"/api/v1/annotations/{job_id}/review",
        json={
            "event_type": "approved",
            "reviewer_id": "reviewer-1",
            "notes": "approved photo",
        },
    )

    list_response = client.get("/api/v1/field-references/approved")

    assert list_response.status_code == 200
    references = list_response.json()
    reference = next(item for item in references if item["job_id"] == job_id)
    assert reference["annotation_mode"] == "stud_locations"
    assert reference["notes"] == "approved photo"
    assert reference["image_url"].endswith("/image")

    image_response = client.get(reference["image_url"])

    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/jpeg"
    assert len(image_response.content) > 0
