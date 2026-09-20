"""Seed a realistic, idempotent demo dataset."""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bson import ObjectId

from app.db import claims_collection, ensure_indexes, users_collection
from app.models import ClaimStatus, User, UserRole
from app.services.auth import hash_password
from app.services.employees import next_employee_id
from app.services.claims import transition
from app.services.duplicates import fingerprint


USERS = [
    ("finance-lead", "Ananya Rao", "ananya.rao@example.com", UserRole.FINANCE, None, 2_500_000),
    ("finance-ops", "Rohan Mehta", "rohan.mehta@example.com", UserRole.FINANCE, None, 2_000_000),
    ("finance-audit", "Nisha Kulkarni", "nisha.kulkarni@example.com", UserRole.FINANCE, None, 2_000_000),
    ("manager-west", "Vikram Shah", "vikram.shah@example.com", UserRole.MANAGER, "finance-lead", 1_800_000),
    ("manager-east", "Priya Nair", "priya.nair@example.com", UserRole.MANAGER, "finance-lead", 1_800_000),
    ("senior-manager", "Arjun Menon", "arjun.menon@example.com", UserRole.MANAGER, "finance-lead", 2_500_000),
    ("staff-asha", "Asha Iyer", "asha.iyer@example.com", UserRole.STAFF, "manager-west", 8_000_00),
    ("staff-rohit", "Rohit Das", "rohit.das@example.com", UserRole.STAFF, "manager-west", 12_000_00),
    ("staff-meera", "Meera Joshi", "meera.joshi@example.com", UserRole.STAFF, "manager-east", 15_000_00),
    ("staff-kabir", "Kabir Singh", "kabir.singh@example.com", UserRole.STAFF, "manager-east", 20_000_00),
    ("staff-tara", "Tara Bose", "tara.bose@example.com", UserRole.STAFF, "manager-east", 25_000_00),
]

ADMIN = ("admin", "System Administrator", "admin@example.com", UserRole.ADMIN, None, 0)


RECEIPTS = [
    ("Meru Cabs PVT LTD Trip 4471 12/09/2026 Rs.214.00", "Meru Cabs", "Taxi", 21400, "2026-09-12"),
    ("SRI KRISHNA BHAVAN bill no 8823 3 pax Total 642/- 14 sep", "Sri Krishna Bhavan", "Meals", 64200, "2026-09-14"),
    ("Uber ride airport to hotel 1,180 rs 9th Sept", "Uber", "Taxi", 118000, "2026-09-09"),
    ("amazon order printer paper + stapler 468 rupees inv IN-88213", "Amazon", "Supplies", 46800, "2026-09-08"),
    ("The Fern hotel room invoice 3321 5 Sep Rs 4200", "The Fern", "Lodging", 420000, "2026-09-05"),
]


def _user(document: dict) -> User:
    """Validate a Mongo user document without leaking its storage id field."""

    payload = {key: value for key, value in document.items() if key != "_id"}
    payload["id"] = str(document["_id"])
    return User.model_validate(payload)


def seed() -> None:
    """Create demo users and claims only when the database is empty."""

    ensure_indexes()
    users = users_collection()
    claims = claims_collection()
    legacy_ids: dict[str, str] = {}
    for user_id, name, email, role, manager_id, limit in [*USERS, ADMIN]:
        designation = "Administrator" if role == UserRole.ADMIN else "Employee"
        password = "Admin@12345" if role == UserRole.ADMIN else "Welcome@123"
        existing = users.find_one({"email": email}) or users.find_one({"_id": user_id})
        generated_id = str(existing["_id"]) if existing else (user_id if role == UserRole.ADMIN else next_employee_id(name, users))
        legacy_ids[user_id] = generated_id
        permanent_manager_id = legacy_ids.get(manager_id) if manager_id else None
        user = User(id=generated_id, name=name, email=email, role=role, designation=designation, manager_id=permanent_manager_id, monthly_limit_paise=limit, password_hash=hash_password(password))
        if existing:
            users.update_one(
                {"_id": existing["_id"]},
                {"$set": {"designation": designation, "manager_id": permanent_manager_id}, "$setOnInsert": {"password_hash": user.password_hash}},
            )
            if not users.find_one({"_id": existing["_id"], "password_hash": {"$exists": True}}):
                users.update_one({"_id": existing["_id"]}, {"$set": {"password_hash": user.password_hash}})
        else:
            users.insert_one({"_id": generated_id, **user.model_dump(exclude={"id"})})

    if claims.count_documents({}):
        print("Seed skipped: demo users upgraded; claims already exist")
        return

    statuses = [ClaimStatus.PAID, ClaimStatus.APPROVED, ClaimStatus.REJECTED, ClaimStatus.SUBMITTED]
    for index in range(40):
        raw_text, merchant, category, amount, expense_date = RECEIPTS[index % len(RECEIPTS)]
        amount += index * 100
        claimant_id = list(users.find({"role": "staff"}, {"_id": 1}))[index % 5]["_id"]
        if index == 39:
            claimant_id = legacy_ids["manager-west"]
            approver_id = legacy_ids["senior-manager"]
        else:
            approver_id = users.find_one({"_id": claimant_id})["manager_id"]
        claim_id = claims.insert_one({
            "claimant_id": claimant_id,
            "approver_id": approver_id,
            "merchant": merchant,
            "category": category,
            "amount_paise": amount,
            "currency": "INR",
            "expense_date": datetime.fromisoformat(expense_date).replace(tzinfo=timezone.utc),
            "receipt_no": None,
            "raw_text": raw_text,
            "source": "text",
            "fingerprint": fingerprint(merchant, amount, datetime.fromisoformat(expense_date).date()),
            "status": ClaimStatus.DRAFT.value,
            "status_history": [],
            "created_at": datetime.now(timezone.utc),
        }).inserted_id
        target = statuses[index % len(statuses)]
        claimant = _user(users.find_one({"_id": claimant_id}))
        transition(str(claim_id), claimant, ClaimStatus.SUBMITTED, claims)
        if target in {ClaimStatus.APPROVED, ClaimStatus.PAID, ClaimStatus.REJECTED}:
            reviewer_id = approver_id
            reviewer = _user(users.find_one({"_id": reviewer_id}))
            if reviewer.role == UserRole.MANAGER and reviewer.id != claimant_id:
                transition(str(claim_id), reviewer, target if target != ClaimStatus.PAID else ClaimStatus.APPROVED, claims)
        if target == ClaimStatus.PAID:
            finance = _user(users.find_one({"_id": "finance-ops"}))
            transition(str(claim_id), finance, ClaimStatus.PAID, claims, payout_ref=f"PAY-2026-09-{index + 1:04d}")
    print("Seed complete: 12 users and 40 claims")


if __name__ == "__main__":
    seed()