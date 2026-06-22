from __future__ import annotations

import os
from typing import Any

from app.storage.gridfs_storage import GridFSStorage
from app.storage.local_storage import LocalStorage


def get_image_storage(backend: str | None = None) -> GridFSStorage | LocalStorage:
    selected = (backend or os.getenv("PERSISTENCE_BACKEND", "mongo")).lower()
    if selected == "mongo":
        return GridFSStorage()
    if selected == "local":
        return LocalStorage()
    raise RuntimeError(f"Unsupported PERSISTENCE_BACKEND: {selected}")


def get_image_storage_for_asset(asset: dict[str, Any]) -> GridFSStorage | LocalStorage:
    storage_backend = asset.get("storage_backend")
    if storage_backend == "gridfs":
        return GridFSStorage()
    if storage_backend == "local":
        return LocalStorage()
    return get_image_storage()
