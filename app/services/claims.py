"""Claim state transitions and authorization rules."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument

from app.models import Claim, ClaimStatus, User, UserRole


class ClaimTransitionError(ValueError):
	"""Raised when a claim cannot make the requested transition."""


ALLOWED_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
	ClaimStatus.DRAFT: {ClaimStatus.SUBMITTED},
	ClaimStatus.SUBMITTED: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
	ClaimStatus.REJECTED: {ClaimStatus.DRAFT},
	ClaimStatus.APPROVED: {ClaimStatus.PAID},
	ClaimStatus.PAID: set(),
}


def _object_id(value: str) -> ObjectId:
	"""Convert a public id safely before it reaches a Mongo filter."""

	try:
		return ObjectId(value)
	except (InvalidId, TypeError):
		raise ClaimTransitionError("claim id is invalid") from None


def _claim_from_document(document: dict[str, Any]) -> Claim:
	"""Convert Mongo's identifier to the model's public string identifier."""

	payload = {**document, "id": str(document["_id"])}
	payload.pop("_id", None)
	return Claim.model_validate(payload)


def _require_actor_can_transition(
	claim: Claim,
	actor: User,
	target: ClaimStatus,
) -> None:
	"""Enforce role and ownership rules for state-changing actions."""

	if target in {ClaimStatus.APPROVED, ClaimStatus.REJECTED}:
		if actor.role != UserRole.MANAGER:
			raise ClaimTransitionError("only a manager can review claims")
		if actor.id != claim.approver_id:
			raise ClaimTransitionError("you are not the assigned approver")
		if actor.id == claim.claimant_id:
			raise ClaimTransitionError("a manager cannot approve their own claim")
	elif target in {ClaimStatus.SUBMITTED, ClaimStatus.DRAFT}:
		if actor.id != claim.claimant_id:
			raise ClaimTransitionError("only the claimant can edit or submit this claim")
	elif target == ClaimStatus.PAID and actor.role != UserRole.FINANCE:
		raise ClaimTransitionError("only finance can pay claims")


def transition(
	claim_id: str,
	actor: User,
	target: ClaimStatus,
	claims: Collection[Any],
	*,
	note: str | None = None,
	now: datetime | None = None,
	payout_ref: str | None = None,
) -> Claim:
	"""Apply one audited state transition, atomically for payment."""

	object_id = _object_id(claim_id)
	document = claims.find_one({"_id": object_id})
	if document is None:
		raise ClaimTransitionError("claim not found")

	claim = _claim_from_document(document)
	if target not in ALLOWED_TRANSITIONS[claim.status]:
		if claim.status == ClaimStatus.PAID:
			raise ClaimTransitionError("paid claims are final")
		raise ClaimTransitionError(
			f"cannot move claim from {claim.status.value} to {target.value}"
		)
	_require_actor_can_transition(claim, actor, target)

	transition_time = now or datetime.now(timezone.utc)
	history_entry = {
		"who": actor.id,
		"from": claim.status.value,
		"to": target.value,
		"when": transition_time,
		"note": note,
	}
	update: dict[str, Any] = {
		"$set": {"status": target.value},
		"$push": {"status_history": history_entry},
	}
	if target == ClaimStatus.PAID:
		if not payout_ref:
			raise ClaimTransitionError("payout reference is required")
		update["$set"].update({"paid_at": transition_time, "payout_ref": payout_ref})

	filter_query = {"_id": object_id, "status": claim.status.value}
	try:
		updated = claims.find_one_and_update(
			filter_query,
			update,
			return_document=ReturnDocument.AFTER,
		)
	except DuplicateKeyError as exc:
		raise ClaimTransitionError("claim conflicts with another stored claim") from exc
	if updated is None:
		if target == ClaimStatus.PAID:
			raise ClaimTransitionError("claim was already paid or changed by another request")
		raise ClaimTransitionError("claim changed before this transition was saved")
	return _claim_from_document(updated)
