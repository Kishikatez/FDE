# Build log

## 2026-09-19

- Scaffolded the FastAPI, MongoDB, Pydantic, service, route, template, test, and deployment layout.
- Added environment-only configuration and claim/user models.
- Implemented the audited state machine and atomic payout transition with mongomock tests.
- Implemented exact, receipt-number, fuzzy, and weak duplicate detection with tests.
- Implemented deterministic receipt parsing and validation for messy Indian receipt formats.
- Added signed demo sessions, server-rendered intake/review, manager/finance actions, monthly reports, and CSV export.
- Added the idempotent seed dataset, Dockerfile, Render configuration, and documentation by hand around the tested services.

Prompts used: the assessment brief supplied in the project workspace and focused implementation requests for each milestone. Problems hit: the first dependency list incorrectly treated HTMX as a Python package, and receipt parsing initially matched a date year as an amount; both were corrected and covered by validation.
