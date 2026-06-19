from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class LocalStorage:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.getenv("LOCAL_STORAGE_ROOT", "backend/storage"))
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

    def rendered_path(self, job_id: str) -> Path:
        return self.rendered_dir / f"{job_id}.jpg"

    def get_rendered_path(self, job_id: str) -> Path:
        return self.rendered_dir / f"{job_id}.jpg"
