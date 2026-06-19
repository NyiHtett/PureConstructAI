from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.db.repositories import get_repository
from app.geometry import parse_calibration_json
from app.model_clients import ModelClientError, get_model_client, get_model_provider_name
from app.renderers.opencv_renderer import render_annotation
from app.schemas import AnnotationMode, AnnotationResponse, ApprovedFieldReferenceSummary, JobStatus, ReviewEventType, ReviewRequest, ReviewResponse
from app.snapper import snap_annotation_spec
from app.storage.local_storage import LocalStorage


app = FastAPI(title="PureConstruct Annotation Renderer")
storage = LocalStorage()


@app.post("/api/v1/annotations", response_model=AnnotationResponse)
async def create_annotation(
    image: UploadFile = File(...),
    annotation_mode: AnnotationMode = Form(...),
    calibration_json: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    wall_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
) -> AnnotationResponse:
    job_id = storage.new_job_id()
    original_path = await storage.save_upload(image, job_id)
    rendered_path = storage.rendered_path(job_id)
    repository = get_repository()

    original_image = cv2.imread(str(original_path))
    if original_image is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable image")
    image_height, image_width = original_image.shape[:2]

    try:
        calibration = parse_calibration_json(calibration_json)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        raw_spec = get_model_client().generate_annotation_spec(
            str(original_path),
            annotation_mode,
            calibration,
            notes,
        )
    except ModelClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    spec = snap_annotation_spec(raw_spec, calibration, annotation_mode)
    render_annotation(str(original_path), spec, str(rendered_path))

    image_asset = repository.create_image_asset(
        {
            "_id": f"{job_id}-original",
            "project_id": project_id,
            "wall_id": wall_id,
            "original_filename": image.filename,
            "width": image_width,
            "height": image_height,
            "content_type": image.content_type or "image/jpeg",
            "storage_backend": "local",
            "local_path": str(original_path),
        }
    )
    calibration_asset = None
    if calibration:
        calibration_asset = repository.create_calibration_payload(
            {
                "_id": f"{job_id}-calibration",
                "image_asset_id": image_asset["_id"],
                "wall_corners_norm": [point.model_dump(mode="json") for point in calibration.wall_corners_norm],
                "stud_centerlines_norm": [stud.model_dump(mode="json") for stud in calibration.stud_centerlines_norm],
                "floor_plane_norm": calibration.floor_plane_norm.model_dump(mode="json")
                if calibration.floor_plane_norm
                else None,
                "created_by": "api",
            }
        )
    repository.create_annotation_job(
        {
            "_id": job_id,
            "image_asset_id": image_asset["_id"],
            "calibration_payload_id": calibration_asset["_id"] if calibration_asset else None,
            "project_id": project_id,
            "wall_id": wall_id,
            "annotation_mode": annotation_mode.value,
            "model_provider": get_model_provider_name(),
            "status": JobStatus.rendered.value,
            "warnings": spec.warnings,
            "completed_at": None,
        }
    )
    repository.save_annotation_spec(
        {
            "_id": f"{job_id}-spec",
            "annotation_job_id": job_id,
            "raw_model_output": raw_spec.model_dump(mode="json"),
            "validated_spec": raw_spec.model_dump(mode="json"),
            "snapped_spec": spec.model_dump(mode="json"),
        }
    )
    repository.save_rendered_asset(
        {
            "_id": f"{job_id}-rendered",
            "annotation_job_id": job_id,
            "content_type": "image/jpeg",
            "storage_backend": "local",
            "local_path": str(rendered_path),
        }
    )

    return AnnotationResponse(
        job_id=job_id,
        annotation_mode=annotation_mode,
        annotated_image_url=f"/api/v1/annotations/{job_id}/image",
        spec=spec,
        warnings=spec.warnings,
    )


@app.get("/api/v1/annotations/{job_id}/image")
def get_annotation_image(job_id: str) -> FileResponse:
    rendered_path = storage.get_rendered_path(job_id)
    if not rendered_path.exists():
        raise HTTPException(status_code=404, detail="Rendered image not found")
    return FileResponse(Path(rendered_path), media_type="image/jpeg")


@app.get("/api/v1/field-references/approved", response_model=list[ApprovedFieldReferenceSummary])
def list_approved_field_references() -> list[ApprovedFieldReferenceSummary]:
    repository = get_repository()
    references = repository.list_approved_field_references()
    return [
        ApprovedFieldReferenceSummary(
            id=reference["_id"],
            job_id=reference["job_id"],
            annotation_mode=reference["annotation_mode"],
            project_id=reference.get("project_id"),
            wall_id=reference.get("wall_id"),
            reviewer_id=reference.get("reviewer_id"),
            notes=reference.get("notes"),
            approved_at=reference["approved_at"],
            image_url=f"/api/v1/field-references/approved/{reference['_id']}/image",
        )
        for reference in references
    ]


@app.get("/api/v1/field-references/approved/{reference_id}/image")
def get_approved_field_reference_image(reference_id: str) -> Response:
    repository = get_repository()
    image = repository.get_approved_field_reference_image(reference_id)
    if not image:
        raise HTTPException(status_code=404, detail="Approved field reference not found")
    data, content_type = image
    return Response(content=data, media_type=content_type)


@app.post("/api/v1/annotations/{job_id}/review", response_model=ReviewResponse)
def review_annotation(job_id: str, payload: ReviewRequest) -> ReviewResponse:
    repository = get_repository()
    existing = repository.get_annotation_job_with_assets(job_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Annotation job not found")

    status = _status_for_review_event(payload.event_type)
    repository.add_review_event(
        {
            "annotation_job_id": job_id,
            "reviewer_id": payload.reviewer_id,
            "event_type": payload.event_type.value,
            "before_spec": None,
            "after_spec": None,
            "notes": payload.notes,
        }
    )
    repository.update_annotation_job_status(job_id, status)
    if status == JobStatus.approved_for_field_reference:
        repository.save_approved_field_reference(job_id, payload.reviewer_id, payload.notes)
    return ReviewResponse(job_id=job_id, status=status, event_type=payload.event_type)


def _status_for_review_event(event_type: ReviewEventType) -> JobStatus:
    if event_type == ReviewEventType.approved:
        return JobStatus.approved_for_field_reference
    if event_type == ReviewEventType.rejected:
        return JobStatus.rejected
    return JobStatus.needs_closer_photo
