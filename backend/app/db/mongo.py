from __future__ import annotations

import os
from typing import Any


def get_mongo_database() -> Any:
    uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("MONGODB_DATABASE") or os.getenv("MONGODB_DB")
    if not uri or not database_name:
        raise RuntimeError("MONGODB_URI and MONGODB_DATABASE are required for MongoDB persistence")

    from pymongo import MongoClient

    return MongoClient(uri)[database_name]
