"""Layered duplicate detection for expense claims."""

import re
import string
from dataclasses import dataclass
from datetime import date
from typing import Any

from rapidfuzz.fuzz import token_set_ratio

from app.models import ClaimStatus


FILLER_WORDS = {"pvt", "ltd", "restaurant", "hotel", "cafe", "the", "and"}


@dataclass(frozen=True)
class DuplicateMatch:
	"""A matching claim and the rule that identified it."""

	claim_id: str
	strength: str
	reason: str
	score: float


def normalise_merchant(merchant: str) -> str:
	"""Create a stable merchant key for exact and fuzzy comparisons."""

	lowered = merchant.lower().translate(str.maketrans("", "", string.punctuation))
	words = [word for word in lowered.split() if word not in FILLER_WORDS]
	return " ".join(words)


def _as_date(value: Any) -> date:
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def _amount_matches(amount: int, other: Any, tolerance: float) -> bool:
	try:
		other_amount = int(other)
	except (TypeError, ValueError):
		return False
	return abs(amount - other_amount) <= amount * tolerance


def fingerprint(merchant: str, amount_paise: int, expense_date: date) -> str:
	"""Build the strong duplicate fingerprint."""

	return f"{normalise_merchant(merchant)}|{amount_paise}|{expense_date.isoformat()}"


def find_duplicate(
	claim: dict[str, Any],
	claims: Any,
	*,
	exclude_id: str | None = None,
) -> DuplicateMatch | None:
	"""Find the highest-priority non-rejected duplicate for a claim."""

	claim_date = _as_date(claim["expense_date"])
	merchant = normalise_merchant(str(claim["merchant"]))
	amount = int(claim["amount_paise"])
	receipt_no = claim.get("receipt_no")
	query: dict[str, Any] = {"status": {"$ne": ClaimStatus.REJECTED.value}}
	if exclude_id:
		query["_id"] = {"$ne": exclude_id}

	weak_match: DuplicateMatch | None = None
	for candidate in claims.find(query):
		candidate_id = str(candidate.get("_id", ""))
		candidate_merchant = normalise_merchant(str(candidate.get("merchant", "")))
		candidate_date = _as_date(candidate["expense_date"])
		candidate_amount = int(candidate["amount_paise"])
		days_apart = abs((claim_date - candidate_date).days)

		if (
			merchant == candidate_merchant
			and amount == candidate_amount
			and claim_date == candidate_date
		):
			return DuplicateMatch(candidate_id, "strong", "same merchant, amount, and date", 100.0)

		candidate_receipt = candidate.get("receipt_no")
		receipt_score = token_set_ratio(merchant, candidate_merchant)
		if receipt_no and candidate_receipt == receipt_no and receipt_score >= 85:
			return DuplicateMatch(candidate_id, "strong", "same receipt number and merchant", receipt_score)

		fuzzy_score = token_set_ratio(merchant, candidate_merchant)
		if amount == candidate_amount and days_apart <= 30 and fuzzy_score >= 85:
			return DuplicateMatch(candidate_id, "strong-fuzzy", "same amount and similar merchant within 30 days", fuzzy_score)

		if (
			claim.get("claimant_id") == candidate.get("claimant_id")
			and claim_date == candidate_date
			and _amount_matches(amount, candidate_amount, 0.02)
		):
			weak_match = DuplicateMatch(candidate_id, "weak", "same claimant and date with amount within 2%", 100.0)

	return weak_match
