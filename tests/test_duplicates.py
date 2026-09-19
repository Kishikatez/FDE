"""Tests for the layered duplicate detector."""

from datetime import date

import mongomock

from app.services.duplicates import find_duplicate, fingerprint, normalise_merchant


def claim(claim_id, merchant, amount, expense_date, claimant="staff-1", status="submitted", receipt_no=None):
    return {
        "_id": claim_id,
        "merchant": merchant,
        "amount_paise": amount,
        "expense_date": expense_date,
        "claimant_id": claimant,
        "status": status,
        "receipt_no": receipt_no,
    }


def test_normalisation_and_fingerprint():
    assert normalise_merchant("MERU CABS PVT LTD") == "meru cabs"
    assert fingerprint("MERU CABS PVT LTD", 21400, date(2026, 9, 12)) == "meru cabs|21400|2026-09-12"


def test_strong_same_day_match():
    collection = mongomock.MongoClient().db.claims
    collection.insert_one(claim("first", "Meru Cabs", 21400, "2026-09-12"))
    match = find_duplicate(claim("second", "MERU CABS PVT LTD", 21400, "2026-09-12"), collection)
    assert match and match.strength == "strong"


def test_strong_receipt_number_match():
    collection = mongomock.MongoClient().db.claims
    collection.insert_one(claim("first", "SRI KRISHNA BHAVAN", 64200, "2026-09-14", receipt_no="8823"))
    match = find_duplicate(claim("second", "Sri Krishna Bhavan Restaurant", 99900, "2026-09-20", receipt_no="8823"), collection)
    assert match and match.strength == "strong"


def test_fuzzy_match_allows_cross_user_duplicate_detection():
    collection = mongomock.MongoClient().db.claims
    collection.insert_one(claim("first", "SRI KRISHNA BHAVAN", 64200, "2026-09-14", claimant="staff-1"))
    match = find_duplicate(claim("second", "Sri Krishna Bhavan Resturant", 64200, "2026-09-28", claimant="staff-2"), collection)
    assert match and match.strength == "strong-fuzzy"


def test_weak_match_warns_only_for_same_claimant():
    collection = mongomock.MongoClient().db.claims
    collection.insert_one(claim("first", "Office Supplies", 10000, "2026-09-14"))
    match = find_duplicate(claim("second", "Another Store", 10100, "2026-09-14"), collection)
    assert match and match.strength == "weak"


def test_rejected_claims_do_not_match():
    collection = mongomock.MongoClient().db.claims
    collection.insert_one(claim("first", "Meru Cabs", 21400, "2026-09-12", status="rejected"))
    assert find_duplicate(claim("second", "Meru Cabs", 21400, "2026-09-12"), collection) is None