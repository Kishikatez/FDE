# Context

_Data flow and co-location context. Use to understand which files work together._

## Critical Flows

_Most central modules by connectivity. Changes here propagate widely._

| Module | Callers | Dependencies |
|--------|---------|--------------|
| `app/db.py` | 1 | 1 |
| `app/config.py` | 1 | 0 |
| `app/main.py` | 0 | 1 |

## Dependency Chains

_Top data/call flow paths. Shows how changes propagate through the codebase._

**Chain 1** (3 modules):
```
app/main.py → app/db.py → app/config.py
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


_Generated: 2026-09-19T05:08:54.452Z_
