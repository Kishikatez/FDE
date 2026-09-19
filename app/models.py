"""Validated domain models shared by routes and services."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(StrEnum):
    STAFF = "staff"
    MANAGER = "manager"
    FINANCE = "finance"


class ClaimCategory(StrEnum):
    TRAVEL = "Travel"
    MEALS = "Meals"
    SUPPLIES = "Supplies"
    TAXI = "Taxi"
    LODGING = "Lodging"
    OTHER = "Other"


class ClaimStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class User(BaseModel):
    """A seeded application user."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    role: UserRole
    manager_id: str | None = None
    monthly_limit_paise: int = Field(ge=0)
    active: bool = True


class StatusHistoryEntry(BaseModel):
    """One audited state transition."""

    model_config = ConfigDict(extra="forbid")

    who: str
    from_status: ClaimStatus | None = Field(default=None, alias="from")
    to: ClaimStatus
    when: datetime
    note: str | None = None


class Claim(BaseModel):
    """A persisted expense claim."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str | None = None
    claimant_id: str
    approver_id: str
    merchant: str = Field(min_length=1, max_length=200)
    category: ClaimCategory
    amount_paise: int = Field(gt=0)
    currency: str = Field(default="INR", pattern="^INR$")
    expense_date: date
    receipt_no: str | None = Field(default=None, max_length=100)
    raw_text: str = Field(max_length=20_000)
    source: str = Field(pattern="^(text|image)$")
    fingerprint: str = ""
    duplicate_of: str | None = None
    duplicate_reason: str | None = None
    duplicate_ack_note: str | None = None
    status: ClaimStatus = ClaimStatus.DRAFT
    status_history: list[StatusHistoryEntry] = Field(default_factory=list)
    created_at: datetime
    paid_at: datetime | None = None
    payout_ref: str | None = None

    @field_validator("merchant", "raw_text")
    @classmethod
    def reject_controlled_empty_values(cls, value: str) -> str:
        """Reject whitespace-only text while retaining original receipt wording."""

        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ClaimDraft(BaseModel):
    """User-correctable structured data produced by receipt parsing."""

    model_config = ConfigDict(extra="forbid")

    merchant: str = Field(min_length=1, max_length=200)
    amount_paise: int = Field(gt=0)
    expense_date: date
    category: ClaimCategory
    receipt_no: str | None = Field(default=None, max_length=100)
    confidence: dict[str, float] = Field(default_factory=dict)


class ReceiptExtraction(BaseModel):
    """Strict provider-neutral extraction result."""

    model_config = ConfigDict(extra="forbid")

    merchant: str | None = Field(default=None, max_length=200)
    amount_paise: int | None = Field(default=None, gt=0)
    expense_date: date | None = None
    category: ClaimCategory = ClaimCategory.OTHER
    receipt_no: str | None = Field(default=None, max_length=100)
