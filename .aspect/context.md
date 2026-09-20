# Context

_Data flow and co-location context. Use to understand which files work together._

## Module Clusters

_Files commonly imported together. Editing one likely requires editing the others._

### App

_Co-imported by: `app/routes/web.py`, `scripts/migrate_employee_ids.py`, `scripts/seed.py`_

- `app/db.py`
- `app/models.py`
- `app/services/auth.py`
- `app/services/claims.py`
- `app/services/duplicates.py`
- _...and 1 more_

### services

_Files in `app/services/` directory_

- `app/services/parsing.py`
- `app/services/payouts.py`
- `app/services/receipt_files.py`
- `app/services/reports.py`

### scripts

_Files in `scripts/` directory_

- `scripts/init_db.py`
- `scripts/migrate_employee_ids.py`
- `scripts/seed.py`

## Critical Flows

_Most central modules by connectivity. Changes here propagate widely._

| Module | Callers | Dependencies |
|--------|---------|--------------|
| `app/models.py` | 6 | 0 |
| `app/routes/web.py` | 1 | 10 |
| `app/db.py` | 5 | 1 |
| `app/services/claims.py` | 3 | 1 |
| `app/config.py` | 3 | 0 |
| `app/services/employees.py` | 3 | 0 |
| `scripts/seed.py` | 0 | 6 |
| `app/services/duplicates.py` | 2 | 1 |

## Dependency Chains

_Top data/call flow paths. Shows how changes propagate through the codebase._

**Chain 1** (3 modules):
```
app/routes/web.py → app/db.py → app/config.py
```

**Chain 2** (3 modules):
```
scripts/init_db.py → app/db.py → app/config.py
```

**Chain 3** (3 modules):
```
scripts/migrate_employee_ids.py → app/db.py → app/config.py
```

**Chain 4** (3 modules):
```
scripts/seed.py → app/db.py → app/config.py
```

## Request Flow Pattern

_How a typical request flows through the architecture._

**Data Flow:**
```
Models (data) → Services (logic) → Handlers (HTTP) → Response
```

---

## Quick Reference

**"What files work together for feature X?"**
→ Check Module Clusters above.

**"Where does data flow from this endpoint?"**
→ Check Critical Flows and Dependency Chains.

**"Where are external connections?"**
→ Check External Integrations.


_Generated: 2026-09-20T17:03:42.041Z_
