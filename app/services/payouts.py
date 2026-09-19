"""Emulated finance payouts."""

from datetime import datetime
from typing import Any

from pymongo.collection import Collection

from app.models import Claim, ClaimStatus, User
from app.services.claims import transition


def make_payout_ref(now: datetime, sequence: int) -> str:
	"""Create a readable fake payout identifier."""

	return f"PAY-{now.year:04d}-{now.month:02d}-{sequence:04d}"


def pay_claim(
	claim_id: str,
	actor: User,
	claims: Collection[Any],
	*,
	payout_ref: str,
	now: datetime | None = None,
) -> Claim:
	"""Pay one approved claim through the atomic workflow transition."""

	return transition(
		claim_id,
		actor,
		ClaimStatus.PAID,
		claims,
		payout_ref=payout_ref,
		now=now,
	)
