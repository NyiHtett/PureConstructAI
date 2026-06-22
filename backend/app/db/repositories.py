from __future__ import annotations

import json
import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from app.db.mongo import get_mongo_database
from app.schemas import JobStatus, ReviewEventType
from app.storage import get_image_storage_for_asset


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA_ROOT = BACKEND_ROOT / "storage" / "metadata"


COLLECTIONS = [
    "projects",
    "image_assets",
    "calibration_payloads",
    "annotation_jobs",
    "annotation_specs",
    "rendered_assets",
    "review_events",
    "approved_field_references",
    "rejected_field_references",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _field_reference_document(
    bundle: dict[str, Any],
    job_id: str,
    reviewer_id: str,
    notes: Optional[str],
    timestamp_key: str,
) -> dict[str, Any]:
    job = bundle["job"]
    rendered_asset = bundle["rendered_assets"][0]
    document = {
        "_id": job_id,
        "job_id": job_id,
        "annotation_mode": job["annotation_mode"],
        "project_id": job.get("project_id"),
        "wall_id": job.get("wall_id"),
        "reviewer_id": reviewer_id,
        "notes": notes,
        "content_type": rendered_asset.get("content_type", "image/jpeg"),
        "storage_backend": rendered_asset.get("storage_backend"),
        timestamp_key: _now(),
    }

    if rendered_asset.get("storage_backend") == "gridfs":
        document["gridfs_file_id"] = rendered_asset["gridfs_file_id"]
    elif rendered_asset.get("storage_backend") == "local":
        document["local_path"] = rendered_asset["local_path"]
    else:
        raise KeyError(f"Unsupported rendered asset storage backend: {rendered_asset.get('storage_backend')}")
    return document


def _strip_image_storage_fields(document: dict[str, Any]) -> dict[str, Any]:
    stripped = dict(document)
    stripped.pop("image_data_base64", None)
    stripped.pop("gridfs_file_id", None)
    stripped.pop("local_path", None)
    return stripped


def _reference_image(document: dict[str, Any]) -> tuple[bytes, str]:
    if document.get("image_data_base64"):
        return base64.b64decode(document["image_data_base64"]), document.get("content_type", "image/jpeg")
    return get_image_storage_for_asset(document).get_file_from_asset(document)


class LocalJsonRepository:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv("METADATA_STORAGE_ROOT", DEFAULT_METADATA_ROOT)).expanduser().resolve()
        for collection in COLLECTIONS:
            (self.root / collection).mkdir(parents=True, exist_ok=True)

    def create_image_asset(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("image_assets", document)

    def create_calibration_payload(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("calibration_payloads", document)

    def create_annotation_job(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("annotation_jobs", document)

    def save_annotation_spec(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("annotation_specs", document)

    def save_rendered_asset(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("rendered_assets", document)

    def add_review_event(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("review_events", document)

    def update_annotation_job_status(self, job_id: str, status: JobStatus) -> None:
        path = self.root / "annotation_jobs" / f"{job_id}.json"
        if not path.exists():
            raise KeyError(job_id)
        document = json.loads(path.read_text())
        document["status"] = status.value
        document["updated_at"] = _now()
        path.write_text(json.dumps(document, indent=2, default=_json_default))

    def get_annotation_job_with_assets(self, job_id: str) -> Optional[dict[str, Any]]:
        job = self._read("annotation_jobs", job_id)
        if not job:
            return None
        rendered_assets = self._find_by("rendered_assets", "annotation_job_id", job_id)
        specs = self._find_by("annotation_specs", "annotation_job_id", job_id)
        reviews = self._find_by("review_events", "annotation_job_id", job_id)
        return {"job": job, "rendered_assets": rendered_assets, "annotation_specs": specs, "review_events": reviews}

    def save_approved_field_reference(self, job_id: str, reviewer_id: str, notes: Optional[str]) -> dict[str, Any]:
        bundle = self.get_annotation_job_with_assets(job_id)
        if not bundle or not bundle["rendered_assets"]:
            raise KeyError(job_id)

        document = _field_reference_document(bundle, job_id, reviewer_id, notes, "approved_at")
        path = self.root / "approved_field_references" / f"{job_id}.json"
        path.write_text(json.dumps(document, indent=2, default=_json_default))
        return document

    def list_approved_field_references(self) -> list[dict[str, Any]]:
        documents = []
        for path in (self.root / "approved_field_references").glob("*.json"):
            document = json.loads(path.read_text())
            documents.append(_strip_image_storage_fields(document))
        return sorted(documents, key=lambda item: item.get("approved_at", ""), reverse=True)

    def get_approved_field_reference_image(self, reference_id: str) -> Optional[tuple[bytes, str]]:
        document = self._read("approved_field_references", reference_id)
        if not document:
            return None
        return _reference_image(document)

    def save_rejected_field_reference(self, job_id: str, reviewer_id: str, notes: Optional[str]) -> dict[str, Any]:
        bundle = self.get_annotation_job_with_assets(job_id)
        if not bundle or not bundle["rendered_assets"]:
            raise KeyError(job_id)

        document = _field_reference_document(bundle, job_id, reviewer_id, notes, "rejected_at")
        path = self.root / "rejected_field_references" / f"{job_id}.json"
        path.write_text(json.dumps(document, indent=2, default=_json_default))
        return document

    def list_rejected_field_references(self) -> list[dict[str, Any]]:
        documents = []
        for path in (self.root / "rejected_field_references").glob("*.json"):
            document = json.loads(path.read_text())
            documents.append(_strip_image_storage_fields(document))
        return sorted(documents, key=lambda item: item.get("rejected_at", ""), reverse=True)

    def get_rejected_field_reference_image(self, reference_id: str) -> Optional[tuple[bytes, str]]:
        document = self._read("rejected_field_references", reference_id)
        if not document:
            return None
        return _reference_image(document)

    def _insert(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        stored = dict(document)
        stored["_id"] = str(stored.get("_id") or uuid4().hex)
        stored.setdefault("created_at", _now())
        path = self.root / collection / f"{stored['_id']}.json"
        path.write_text(json.dumps(stored, indent=2, default=_json_default))
        return stored

    def _read(self, collection: str, document_id: str) -> Optional[dict[str, Any]]:
        path = self.root / collection / f"{document_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def _find_by(self, collection: str, key: str, value: str) -> list[dict[str, Any]]:
        documents = []
        for path in (self.root / collection).glob("*.json"):
            document = json.loads(path.read_text())
            if document.get(key) == value:
                documents.append(document)
        return documents


class MongoRepository:
    def __init__(self) -> None:
        self.db = get_mongo_database()

    def create_image_asset(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("image_assets", document)

    def create_calibration_payload(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("calibration_payloads", document)

    def create_annotation_job(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("annotation_jobs", document)

    def save_annotation_spec(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("annotation_specs", document)

    def save_rendered_asset(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("rendered_assets", document)

    def add_review_event(self, document: dict[str, Any]) -> dict[str, Any]:
        return self._insert("review_events", document)

    def update_annotation_job_status(self, job_id: str, status: JobStatus) -> None:
        self.db.annotation_jobs.update_one({"_id": job_id}, {"$set": {"status": status.value, "updated_at": _now()}})

    def get_annotation_job_with_assets(self, job_id: str) -> Optional[dict[str, Any]]:
        job = self.db.annotation_jobs.find_one({"_id": job_id})
        if not job:
            return None
        return {
            "job": job,
            "rendered_assets": list(self.db.rendered_assets.find({"annotation_job_id": job_id})),
            "annotation_specs": list(self.db.annotation_specs.find({"annotation_job_id": job_id})),
            "review_events": list(self.db.review_events.find({"annotation_job_id": job_id})),
        }

    def save_approved_field_reference(self, job_id: str, reviewer_id: str, notes: Optional[str]) -> dict[str, Any]:
        bundle = self.get_annotation_job_with_assets(job_id)
        if not bundle or not bundle["rendered_assets"]:
            raise KeyError(job_id)

        document = _field_reference_document(bundle, job_id, reviewer_id, notes, "approved_at")
        self.db.approved_field_references.replace_one({"_id": job_id}, document, upsert=True)
        return document

    def list_approved_field_references(self) -> list[dict[str, Any]]:
        return [
            _strip_image_storage_fields(document)
            for document in self.db.approved_field_references.find({}).sort("approved_at", -1)
        ]

    def get_approved_field_reference_image(self, reference_id: str) -> Optional[tuple[bytes, str]]:
        document = self.db.approved_field_references.find_one({"_id": reference_id})
        if not document:
            return None
        return _reference_image(document)

    def save_rejected_field_reference(self, job_id: str, reviewer_id: str, notes: Optional[str]) -> dict[str, Any]:
        bundle = self.get_annotation_job_with_assets(job_id)
        if not bundle or not bundle["rendered_assets"]:
            raise KeyError(job_id)

        document = _field_reference_document(bundle, job_id, reviewer_id, notes, "rejected_at")
        self.db.rejected_field_references.replace_one({"_id": job_id}, document, upsert=True)
        return document

    def list_rejected_field_references(self) -> list[dict[str, Any]]:
        return [
            _strip_image_storage_fields(document)
            for document in self.db.rejected_field_references.find({}).sort("rejected_at", -1)
        ]

    def get_rejected_field_reference_image(self, reference_id: str) -> Optional[tuple[bytes, str]]:
        document = self.db.rejected_field_references.find_one({"_id": reference_id})
        if not document:
            return None
        return _reference_image(document)

    def _insert(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        stored = dict(document)
        stored["_id"] = str(stored.get("_id") or uuid4().hex)
        stored.setdefault("created_at", _now())
        self.db[collection].insert_one(stored)
        return stored


def get_repository() -> LocalJsonRepository | MongoRepository:
    selected = os.getenv("PERSISTENCE_BACKEND", "mongo").lower()
    if selected == "mongo":
        return MongoRepository()
    if selected == "local":
        return LocalJsonRepository()
    raise RuntimeError(f"Unsupported PERSISTENCE_BACKEND: {selected}")
