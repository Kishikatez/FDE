"""Promote generated employee IDs to permanent MongoDB user IDs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import claims_collection, ensure_indexes, users_collection
from app.services.employees import migrate_employee_ids


if __name__ == "__main__":
    ensure_indexes()
    mapping = migrate_employee_ids(users_collection(), claims_collection())
    print(f"Migrated {len(mapping)} employee IDs")
    for old_id, new_id in sorted(mapping.items()):
        print(f"{old_id} -> {new_id}")
