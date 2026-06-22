from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from app.db.mongo import get_mongo_database


class GridFSStorage:
    def __init__(self) -> None:
        import gridfs

        self.db = get_mongo_database()
        self.fs = gridfs.GridFS(self.db)

    def new_job_id(self) -> str:
        return uuid4().hex

    def save_file(self, path: str | Path, filename: str, content_type: str = "image/jpeg") -> str:
        with Path(path).open("rb") as file:
            return str(self.fs.put(file, filename=filename, content_type=content_type))

    def persist_original_file(self, source_path: str | Path, job_id: str, content_type: str) -> dict[str, Any]:
        return self._persist_file(source_path, f"{job_id}-original.jpg", content_type)

    def persist_rendered_file(self, source_path: str | Path, job_id: str, content_type: str) -> dict[str, Any]:
        return self._persist_file(source_path, f"{job_id}-rendered.jpg", content_type)

    def get_file(self, file_id: Any) -> Any:
        from bson import ObjectId

        object_id = ObjectId(file_id) if isinstance(file_id, str) else file_id
        return self.fs.get(object_id)

    def get_file_from_asset(self, asset: dict[str, Any]) -> tuple[bytes, str]:
        file_id = asset.get("gridfs_file_id")
        if not file_id:
            raise FileNotFoundError("GridFS asset is missing gridfs_file_id")
        file = self.get_file(file_id)
        return file.read(), asset.get("content_type") or getattr(file, "content_type", "image/jpeg")

    def _persist_file(self, source_path: str | Path, filename: str, content_type: str) -> dict[str, Any]:
        return {
            "storage_backend": "gridfs",
            "gridfs_file_id": self.save_file(source_path, filename, content_type),
            "content_type": content_type,
        }
