"""MongoDB client and collection setup."""

from functools import lru_cache
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import get_settings


@lru_cache
def get_client() -> MongoClient[Any]:
    """Create one synchronous MongoDB client for the process."""

    settings = get_settings()
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5_000)


def get_database() -> Database[Any]:
    """Return the configured database."""

    return get_client()[get_settings().mongodb_db]


def users_collection() -> Collection[Any]:
    """Return the users collection."""

    return get_database()["users"]


def claims_collection() -> Collection[Any]:
    """Return the claims collection."""

    return get_database()["claims"]


def ensure_indexes() -> None:
    """Create collections and indexes required by the application."""

    database = get_database()
    existing_collections = set(database.list_collection_names())
    if "users" not in existing_collections:
        database.create_collection("users")
    if "claims" not in existing_collections:
        database.create_collection("claims")

    users_collection().create_index([("email", ASCENDING)], unique=True, name="users_email_unique")
    claims = claims_collection()
    claims.create_index([("status", ASCENDING)], name="claims_status")
    claims.create_index(
        [("claimant_id", ASCENDING), ("expense_date", ASCENDING)],
        name="claims_claimant_date",
    )
    claims.create_index(
        [("fingerprint", ASCENDING)],
        name="claims_strong_fingerprint",
        unique=True,
        partialFilterExpression={
            "status": {"$in": ["draft", "submitted", "approved", "paid"]},
            "fingerprint": {"$type": "string", "$gt": ""},
        },
    )
