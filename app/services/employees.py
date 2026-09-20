"""Employee identity helpers."""

import re
from typing import Any


def employee_id_prefix(name: str) -> str:
    """Return the normalized first-name prefix used for employee IDs."""

    first_name = name.strip().split()[0] if name.strip() else "employee"
    prefix = re.sub(r"[^a-z0-9]", "", first_name.lower())
    return prefix or "employee"


def next_employee_id(name: str, users: Any) -> str:
    """Generate the next available first-name plus global three-digit serial ID."""

    prefix = employee_id_prefix(name)
    highest = 0
    for employee in users.find({}, {"_id": 1}):
        match = re.search(r"(\d{3})$", str(employee.get("_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1:03d}"


def migrate_employee_ids(users: Any, claims: Any) -> dict[str, str]:
    """Promote generated employee IDs to Mongo IDs and update all references."""

    mapping: dict[str, str] = {}
    employees = list(users.find({"role": {"$ne": "admin"}}))
    for employee in employees:
        old_id = str(employee["_id"])
        new_id = str(employee.get("employee_id") or old_id)
        if old_id != new_id:
            mapping[old_id] = new_id

    for employee in employees:
        old_id = str(employee["_id"])
        new_id = mapping.get(old_id)
        if not new_id:
            users.update_one({"_id": old_id}, {"$unset": {"employee_id": ""}})
            continue
        replacement = {key: value for key, value in employee.items() if key not in {"_id", "employee_id"}}
        replacement["_id"] = new_id
        users.delete_one({"_id": old_id})
        users.insert_one(replacement)

    for old_id, new_id in mapping.items():
        users.update_many({"manager_id": old_id}, {"$set": {"manager_id": new_id}})
        claims.update_many({"claimant_id": old_id}, {"$set": {"claimant_id": new_id}})
        claims.update_many({"approver_id": old_id}, {"$set": {"approver_id": new_id}})
        users.delete_one({"_id": old_id})
    return mapping
