# Map

_Symbol index with signatures and conventions. Use to find types, functions, and coding patterns._

## Symbol Index

_Functions, classes, and exports with call relationships._

### `app/db.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `get_client` | function | `def get_client()` | `app/main.py` |
| `get_database` | function | `def get_database()` | `app/main.py` |
| `users_collection` | function | `def users_collection()` | `app/main.py` |
| `claims_collection` | function | `def claims_collection()` | `app/main.py` |
| `ensure_indexes` | function | `def ensure_indexes()` | `app/main.py` |

### `app/config.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `Settings` | class | `class Settings(BaseSettings)` | `app/db.py` |
| `get_settings` | function | `def get_settings()` | `app/db.py` |

### `app/main.py`

| Symbol | Kind | Signature | Used In (files) |
|--------|------|-----------|----------------|
| `healthz` | function | `def healthz()` | — |

---

## Conventions

_Naming patterns and styles. Follow these for consistency._

### File Naming

| Pattern | Example | Count |
|---------|---------|-------|
| snake_case | `__init__.py` | 3 |

### Function Naming

- `get_*` → `get_settings` (3 occurrences)


_Generated: 2026-09-19T05:10:38.265Z_
