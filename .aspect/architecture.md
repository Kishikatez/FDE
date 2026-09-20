# Architecture

_Read this first. Describes the project layout and "Do Not Break" zones._

**Files:** 23 | **Dependencies:** 34 | **Cycles:** 0

## ⚠️ High-Risk Architectural Hubs

> **These files are architectural load-bearing walls.**
> Modify with extreme caution. Do not change signatures without checking `map.md`.

| Rank | File | Imports | Imported By | Risk |
|------|------|---------|-------------|------|
| 1 | `app/routes/web.py` | 10 | 1 | 🟢 Low |
| 2 | `app/models.py` | 0 | 6 | 🟡 Medium |
| 3 | `app/db.py` | 1 | 5 | 🟡 Medium |
| 4 | `scripts/seed.py` | 6 | 0 | 🟢 Low |
| 5 | `app/services/claims.py` | 1 | 3 | 🟢 Low |
| 6 | `app/services/duplicates.py` | 1 | 2 | 🟢 Low |
| 7 | `app/services/parsing.py` | 2 | 1 | 🟢 Low |
| 8 | `app/services/payouts.py` | 2 | 1 | 🟢 Low |
| 9 | `app/config.py` | 0 | 3 | 🟢 Low |
| 10 | `app/main.py` | 3 | 0 | 🟢 Low |
| 11 | `app/services/employees.py` | 0 | 3 | 🟢 Low |

### Hub Details & Blast Radius

_Blast radius = direct dependents + their dependents (2 levels)._

**1. `app/routes/web.py`** — Blast radius: 1 files
   - Direct dependents: 1
   - Indirect dependents: ~0

   Imported by (1 files):
   - `app/main.py`

**2. `app/models.py`** — Blast radius: 10 files
   - Direct dependents: 6
   - Indirect dependents: ~4

   Imported by (6 files):
   - `app/routes/web.py`
   - `app/services/claims.py`
   - `app/services/duplicates.py`
   - `app/services/parsing.py`
   - `app/services/payouts.py`
   - _...and 1 more_

**3. `app/db.py`** — Blast radius: 6 files
   - Direct dependents: 5
   - Indirect dependents: ~1

   Imported by (5 files):
   - `app/main.py`
   - `app/routes/web.py`
   - `scripts/init_db.py`
   - `scripts/migrate_employee_ids.py`
   - `scripts/seed.py`

## Entry Points

_Where code execution begins. Categorized by type with detection confidence._

### Runtime Entry Points

_Server handlers, API routes, application entry._

- 🟢 `app/routes/web.py`: FastAPI (25 routes)
- 🟢 `app/main.py`: FastAPI (1 routes)

### Runnable Scripts / Tooling

_CLI tools, build scripts, standalone utilities._

- 🟡 `scripts/init_db.py`: Script entry (__main__)
- 🟡 `scripts/migrate_employee_ids.py`: Script entry (__main__)
- 🟡 `scripts/seed.py`: Script entry (__main__)

## Directory Layout

| Directory | Files | Purpose |
|-----------|-------|--------|
| `app/services/` | 9 | Services |
| `app/` | 5 | General |
| `scripts/` | 4 | General |
| `app/routes/` | 2 | General |

## Tests

**Test files:** 3 | **Dirs:** tests


_Generated: 2026-09-20T17:11:18.563Z_
