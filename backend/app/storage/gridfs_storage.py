from __future__ import annotations

from pathlib import Path
from typing import Any

from app.db.mongo import get_mongo_database


class GridFSStorage:
    def __init__(self) -> None:
        import gridfs

        self.db = get_mongo_database()
        self.fs = gridfs.GridFS(self.db)

    def save_file(self, path: str | Path, filename: str, content_type: str = "image/jpeg") -> Any:
        with Path(path).open("rb") as file:
            return self.fs.put(file, filename=filename, content_type=content_type)

    def get_file(self, file_id: Any) -> Any:
        return self.fs.get(file_id)
