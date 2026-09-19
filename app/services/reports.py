"""Mongo-backed monthly spend and limit reports."""

from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Any

from pymongo.collection import Collection


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
	"""Return inclusive-start and exclusive-end UTC bounds for expense month."""

	start = datetime(year, month, 1, tzinfo=timezone.utc)
	if month == 12:
		end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
	else:
		end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
	return start, end


def monthly_report(claims: Collection[Any], users: Collection[Any], year: int, month: int) -> dict[str, Any]:
	"""Build finance report sections with Mongo aggregation pipelines."""

	start, end = month_bounds(year, month)
	match = {"expense_date": {"$gte": start, "$lt": end}, "status": {"$ne": "rejected"}}
	by_person_category = list(claims.aggregate([
		{"$match": match},
		{"$group": {"_id": {"claimant_id": "$claimant_id", "category": "$category"}, "total_paise": {"$sum": "$amount_paise"}, "claims": {"$sum": 1}}},
		{"$sort": {"_id.claimant_id": 1, "_id.category": 1}},
	]))
	by_category = list(claims.aggregate([
		{"$match": match},
		{"$group": {"_id": "$category", "total_paise": {"$sum": "$amount_paise"}}},
		{"$sort": {"_id": 1}},
	]))
	by_person = list(claims.aggregate([
		{"$match": match},
		{"$group": {"_id": "$claimant_id", "total_paise": {"$sum": "$amount_paise"}}},
		{"$sort": {"total_paise": -1}},
	]))
	status_totals = list(claims.aggregate([
		{"$match": {"expense_date": {"$gte": start, "$lt": end}}},
		{"$group": {"_id": "$status", "total_paise": {"$sum": "$amount_paise"}, "claims": {"$sum": 1}}},
	]))
	user_map = {str(user["_id"]): user for user in users.find({}, {"name": 1, "monthly_limit_paise": 1})}
	people = []
	for row in by_person:
		person = user_map.get(str(row["_id"]), {})
		total = int(row["total_paise"])
		limit = int(person.get("monthly_limit_paise", 0))
		percent = (total / limit * 100) if limit else 0
		people.append({"user_id": str(row["_id"]), "name": person.get("name", "Unknown"), "total_paise": total, "limit_paise": limit, "percent": percent, "status": "OVER" if percent > 100 else "NEAR" if percent >= 90 else "OK"})
	return {"year": year, "month": month, "by_person_category": by_person_category, "by_category": by_category, "people": people, "status_totals": status_totals}


def limit_state(total_paise: int, limit_paise: int) -> str:
	"""Classify monthly spend without blocking submission."""

	if not limit_paise or total_paise > limit_paise:
		return "OVER" if limit_paise else "NO LIMIT"
	return "NEAR" if total_paise >= limit_paise * 0.9 else "OK"
