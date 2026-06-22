from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE_ROOT = BACKEND_ROOT / "storage"


class LocalStorage:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv("LOCAL_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)).expanduser().resolve()
        self.originals_dir = self.root / "originals"
        self.rendered_dir = self.root / "rendered"
        self.originals_dir.mkdir(parents=True, exist_ok=True)
        self.rendered_dir.mkdir(parents=True, exist_ok=True)

    def new_job_id(self) -> str:
        return uuid4().hex

    async def save_upload(self, image: UploadFile, job_id: str) -> Path:
        path = self.originals_dir / f"{job_id}.jpg"
        content = await image.read()
        path.write_bytes(content)
        return path

    def persist_original_file(self, source_path: str | Path, job_id: str, content_type: str) -> dict[str, Any]:
        return self._copy_file(source_path, self.originals_dir / f"{job_id}.jpg", content_type)

    def persist_rendered_file(self, source_path: str | Path, job_id: str, content_type: str) -> dict[str, Any]:
        return self._copy_file(source_path, self.rendered_dir / f"{job_id}.jpg", content_type)

    def get_file_from_asset(self, asset: dict[str, Any]) -> tuple[bytes, str]:
        local_path = asset.get("local_path")
        if not local_path:
            raise FileNotFoundError("Local asset is missing local_path")
        return Path(local_path).read_bytes(), asset.get("content_type", "image/jpeg")

    def rendered_path(self, job_id: str) -> Path:
        return self.rendered_dir / f"{job_id}.jpg"

    def get_rendered_path(self, job_id: str) -> Path:
        return self.rendered_dir / f"{job_id}.jpg"

    def _copy_file(self, source_path: str | Path, destination_path: Path, content_type: str) -> dict[str, Any]:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination_path)
        return {
            "storage_backend": "local",
            "local_path": str(destination_path),
            "content_type": content_type,
        }
