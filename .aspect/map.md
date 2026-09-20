# Map

_Symbol index with signatures and conventions. Use to find types, functions, and coding patterns._

## Symbol Index

_Functions, classes, and exports with call relationships._

### `app/models.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `UserRole` | class | `class UserRole(StrEnum)` | `(+1 more)`, `routes/web.py` |
| `ClaimCategory` | class | `class ClaimCategory(StrEnum)` | `(+1 more)`, `routes/web.py` |
| `ClaimStatus` | class | `class ClaimStatus(StrEnum)` | `(+1 more)`, `routes/web.py` |
| `User` | class | `class User(BaseModel)` | `(+1 more)`, `routes/web.py` |
| `StatusHistoryEntry` | class | `class StatusHistoryEntry(BaseModel)` | `(+1 more)`, `routes/web.py` |
| `Claim` | class | `class Claim(BaseModel)` | `(+1 more)`, `routes/web.py` |
| `reject_controlled_empty_values` | method | `def reject_controlled_empty_values(value)` | `(+1 more)`, `routes/web.py` |
| `ClaimDraft` | class | `class ClaimDraft(BaseModel)` | `(+1 more)`, `routes/web.py` |
| `ReceiptExtraction` | class | `class ReceiptExtraction(BaseModel)` | `(+1 more)`, `routes/web.py` |

### `app/routes/web.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `format_paise` | function | `def format_paise(value)` | `app/main.py` |
| `home` | function | `def home(request)` | `app/main.py` |
| `sign_in` | function | `def sign_in(request)` | `app/main.py` |
| `sign_in_submit` | function | `def sign_in_submit(request, user_id, password, csrf_token)` | `app/main.py` |
| `sign_out` | function | `def sign_out(request, csrf_token)` | `app/main.py` |
| `dashboard` | function | `def dashboard(request, view)` | `app/main.py` |
| `new_claim` | function | `def new_claim(request)` | `app/main.py` |
| `new_claim_submit` | function | `def new_claim_submit(request, files, csrf_token)` | `app/main.py` |
| `parse_batch` | function | `def parse_batch(request, files, csrf_token)` | `app/main.py` |
| `admin_employees` | function | `def admin_employees(request)` | `app/main.py` |
| `enroll_employee` | function | `def enroll_employee(request, name, email, designation)` | `app/main.py` |
| `employee_detail` | function | `def employee_detail(request, employee_id)` | `app/main.py` |

_+14 more symbols_

### `app/db.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `get_client` | function | `def get_client()` | `app/main.py`, `routes/web.py` |
| `get_database` | function | `def get_database()` | `app/main.py`, `routes/web.py` |
| `users_collection` | function | `def users_collection()` | `app/main.py`, `routes/web.py` |
| `claims_collection` | function | `def claims_collection()` | `app/main.py`, `routes/web.py` |
| `ensure_indexes` | function | `def ensure_indexes()` | `app/main.py`, `routes/web.py` |

### `app/services/claims.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `ClaimTransitionError` | class | `class ClaimTransitionError(ValueError)` | `routes/web.py`, `scripts/seed.py` |
| `transition` | function | `def transition(claim_id, actor, target, claims)` | `routes/web.py`, `scripts/seed.py` |

### `app/services/duplicates.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `DuplicateMatch` | class | `class DuplicateMatch` | `routes/web.py`, `scripts/seed.py` |
| `normalise_merchant` | function | `def normalise_merchant(merchant)` | `routes/web.py`, `scripts/seed.py` |
| `fingerprint` | function | `def fingerprint(merchant, amount_paise, expense_date)` | `routes/web.py`, `scripts/seed.py` |
| `find_duplicate` | function | `def find_duplicate(claim, claims, exclude_id)` | `routes/web.py`, `scripts/seed.py` |

### `app/config.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `Settings` | class | `class Settings(BaseSettings)` | `app/db.py`, `app/main.py` |
| `get_settings` | function | `def get_settings()` | `app/db.py`, `app/main.py` |

### `app/services/employees.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `employee_id_prefix` | function | `def employee_id_prefix(name)` | `routes/web.py`, `scripts/migrate_employee_ids.py` |
| `next_employee_id` | function | `def next_employee_id(name, users)` | `routes/web.py`, `scripts/migrate_employee_ids.py` |
| `migrate_employee_ids` | function | `def migrate_employee_ids(users, claims)` | `routes/web.py`, `scripts/migrate_employee_ids.py` |

### `app/services/parsing.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `ReceiptParseError` | class | `class ReceiptParseError(ValueError)` | `routes/web.py` |
| `parse_fallback` | function | `def parse_fallback(text, today)` | `routes/web.py` |
| `parse_receipt` | function | `def parse_receipt(text, today)` | `routes/web.py` |

### `app/services/payouts.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `make_payout_ref` | function | `def make_payout_ref(now, sequence)` | `routes/web.py` |
| `pay_claim` | function | `def pay_claim(claim_id, actor, claims, payout_ref)` | `routes/web.py` |

### `scripts/seed.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `seed` | function | `def seed()` | — |

### `app/services/auth.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `hash_password` | function | `def hash_password(password)` | `routes/web.py`, `scripts/seed.py` |
| `verify_password` | function | `def verify_password(password, encoded)` | `routes/web.py`, `scripts/seed.py` |

### `app/main.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `initialize_database` | function | `def initialize_database()` | — |
| `permission_error` | function | `def permission_error(request, exc)` | — |
| `healthz` | function | `def healthz()` | — |

### `app/services/receipt_files.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `ReceiptFileError` | class | `class ReceiptFileError(ValueError)` | `routes/web.py` |
| `extract_receipt_text` | function | `def extract_receipt_text(filename, content)` | `routes/web.py` |

### `app/services/reports.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `month_bounds` | function | `def month_bounds(year, month)` | `routes/web.py` |
| `monthly_report` | function | `def monthly_report(claims, users, year, month)` | `routes/web.py` |
| `limit_state` | function | `def limit_state(total_paise, limit_paise)` | `routes/web.py` |

### `scripts/init_db.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `main` | function | `def main()` | — |

### `tests/test_claims.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `user` | function | `def user(user_id, role, manager_id)` | — |
| `claims` | function | `def claims()` | — |
| `test_valid_workflow_and_history` | function | `def test_valid_workflow_and_history(claims)` | — |
| `test_paid_is_terminal` | function | `def test_paid_is_terminal(claims)` | — |
| `test_manager_cannot_approve_own_claim` | function | `def test_manager_cannot_approve_own_claim(claims)` | — |
| `test_wrong_manager_cannot_approve` | function | `def test_wrong_manager_cannot_approve(claims)` | — |
| `test_double_pay_is_rejected_by_status_filter` | function | `def test_double_pay_is_rejected_by_status_filter(claims)` | — |

### `tests/test_duplicates.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `claim` | function | `def claim(claim_id, merchant, amount, expense_date)` | — |
| `test_normalisation_and_fingerprint` | function | `def test_normalisation_and_fingerprint()` | — |
| `test_strong_same_day_match` | function | `def test_strong_same_day_match()` | — |
| `test_strong_receipt_number_match` | function | `def test_strong_receipt_number_match()` | — |
| `test_fuzzy_match_allows_cross_user_duplicate_detection` | function | `def test_fuzzy_match_allows_cross_user_duplicate_detection()` | — |
| `test_weak_match_warns_only_for_same_claimant` | function | `def test_weak_match_warns_only_for_same_claimant()` | — |
| `test_rejected_claims_do_not_match` | function | `def test_rejected_claims_do_not_match()` | — |

### `tests/test_parsing.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `test_parses_messy_seed_receipt` | function | `def test_parses_messy_seed_receipt()` | — |
| `test_parses_rupees_suffix_and_invoice` | function | `def test_parses_rupees_suffix_and_invoice()` | — |
| `test_rejects_future_and_old_dates` | function | `def test_rejects_future_and_old_dates()` | — |
| `test_rejects_non_positive_amount` | function | `def test_rejects_non_positive_amount()` | — |

---

## Conventions

_Naming patterns and styles. Follow these for consistency._

### File Naming

| Pattern | Example | Count |
|---------|---------|-------|
| snake_case | `__init__.py` | 7 |

**Use:** snake_case for new files.

### Function Naming

- `get_*` → `get_settings` (3 occurrences)
- `delete_*` → `delete_employee` (1 occurrences)


_Generated: 2026-09-20T17:11:18.614Z_
