"""Focused tests for the claim workflow milestone."""

from datetime import datetime, timezone

import mongomock
import pytest
from bson import ObjectId

from app.models import ClaimCategory, ClaimStatus, User, UserRole
from app.services.claims import ClaimTransitionError, transition
from app.services.payouts import pay_claim


NOW = datetime(2026, 9, 19, tzinfo=timezone.utc)


def user(user_id: str, role: UserRole, manager_id: str | None = None) -> User:
    return User(
        id=user_id,
        name=user_id,
        email=f"{user_id}@example.com",
        role=role,
        manager_id=manager_id,
        monthly_limit_paise=1_000_000,
    )


@pytest.fixture
def claims():
    collection = mongomock.MongoClient().db.claims
    claimant = user("staff-1", UserRole.STAFF, "manager-1")
    collection.insert_one(
        {
            "_id": ObjectId("68dce0000000000000000001"),
            "claimant_id": claimant.id,
            "approver_id": "manager-1",
            "merchant": "Meru Cabs",
            "category": ClaimCategory.TAXI.value,
            "amount_paise": 21400,
            "currency": "INR",
            "expense_date": "2026-09-12",
            "raw_text": "Meru Cabs Rs 214",
            "source": "text",
            "fingerprint": "",
            "status": ClaimStatus.DRAFT.value,
            "status_history": [],
            "created_at": NOW,
        }
    )
    return collection


CLAIM_ID = "68dce0000000000000000001"


def test_valid_workflow_and_history(claims):
    staff = user("staff-1", UserRole.STAFF, "manager-1")
    manager = user("manager-1", UserRole.MANAGER)
    finance = user("finance-1", UserRole.FINANCE)

    transition(CLAIM_ID, staff, ClaimStatus.SUBMITTED, claims, now=NOW)
    transition(CLAIM_ID, manager, ClaimStatus.APPROVED, claims, now=NOW)
    paid = pay_claim(CLAIM_ID, finance, claims, payout_ref="PAY-2026-09-0001", now=NOW)

    assert paid.status == ClaimStatus.PAID
    assert paid.payout_ref == "PAY-2026-09-0001"
    assert [entry.to for entry in paid.status_history] == [
        ClaimStatus.SUBMITTED,
        ClaimStatus.APPROVED,
        ClaimStatus.PAID,
    ]


def test_paid_is_terminal(claims):
    staff = user("staff-1", UserRole.STAFF, "manager-1")
    manager = user("manager-1", UserRole.MANAGER)
    finance = user("finance-1", UserRole.FINANCE)
    transition(CLAIM_ID, staff, ClaimStatus.SUBMITTED, claims, now=NOW)
    transition(CLAIM_ID, manager, ClaimStatus.APPROVED, claims, now=NOW)
    pay_claim(CLAIM_ID, finance, claims, payout_ref="PAY-2026-09-0001", now=NOW)

    with pytest.raises(ClaimTransitionError, match="paid claims are final"):
        transition(CLAIM_ID, finance, ClaimStatus.APPROVED, claims, now=NOW)


def test_manager_cannot_approve_own_claim(claims):
    claims.update_one({"_id": ObjectId(CLAIM_ID)}, {"$set": {"claimant_id": "manager-1"}})
    manager = user("manager-1", UserRole.MANAGER)
    transition(CLAIM_ID, manager, ClaimStatus.SUBMITTED, claims, now=NOW)
    with pytest.raises(ClaimTransitionError, match="cannot approve their own"):
        transition(CLAIM_ID, manager, ClaimStatus.APPROVED, claims, now=NOW)


def test_wrong_manager_cannot_approve(claims):
    staff = user("staff-1", UserRole.STAFF, "manager-1")
    wrong_manager = user("manager-2", UserRole.MANAGER)
    transition(CLAIM_ID, staff, ClaimStatus.SUBMITTED, claims, now=NOW)
    with pytest.raises(ClaimTransitionError, match="not the assigned approver"):
        transition(CLAIM_ID, wrong_manager, ClaimStatus.APPROVED, claims, now=NOW)


def test_double_pay_is_rejected_by_status_filter(claims):
    staff = user("staff-1", UserRole.STAFF, "manager-1")
    manager = user("manager-1", UserRole.MANAGER)
    finance = user("finance-1", UserRole.FINANCE)
    transition(CLAIM_ID, staff, ClaimStatus.SUBMITTED, claims, now=NOW)
    transition(CLAIM_ID, manager, ClaimStatus.APPROVED, claims, now=NOW)
    pay_claim(CLAIM_ID, finance, claims, payout_ref="PAY-2026-09-0001", now=NOW)

    with pytest.raises(ClaimTransitionError, match="paid claims are final"):
        pay_claim(CLAIM_ID, finance, claims, payout_ref="PAY-2026-09-0002", now=NOW)