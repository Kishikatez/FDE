# Decisions

## Server-rendered stack

FastAPI and Jinja2 keep the deployment small and make role checks visible on the server. Forms are compatible with HTMX enhancement without requiring a build system.

## Duplicate strategy

Exact normalized merchant/amount/date catches obvious repeats. Receipt-number matching and rapidfuzz token similarity catch wording changes and refiled receipts. A weaker same-person warning avoids blocking legitimate corrections.

## Money as integer paise

All persisted amounts are integers. Currency formatting happens only at the presentation boundary, so calculations never depend on binary floating-point behavior.
