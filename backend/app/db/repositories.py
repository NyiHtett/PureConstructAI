from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from app.db.mongo import get_mongo_database
from app.schemas import JobStatus, ReviewEventType


COLLECTIONS = [
    "projects",
    "image_assets",
    "calibration_payloads",
    "annotation_jobs",
    "annotation_specs",
    "rendered_assets",
    "review_events",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class LocalJsonRepository:
    def __init__(self, root: str | Path = "backend/storage/metadata") -> None:
        self.root = Path(root)
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

    def _insert(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        stored = dict(document)
        stored["_id"] = str(stored.get("_id") or uuid4().hex)
        stored.setdefault("created_at", _now())
        self.db[collection].insert_one(stored)
        return stored


def get_repository() -> LocalJsonRepository | MongoRepository:
    if os.getenv("PERSISTENCE_BACKEND", "local").lower() == "mongo":
        return MongoRepository()
    return LocalJsonRepository()
