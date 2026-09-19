# Database Schema

This project uses MongoDB, so there are collections rather than relational tables. MongoDB creates the database when the first collection is created. `python scripts/init_db.py` explicitly creates the `users` and `claims` collections and their indexes. The web application also performs this initialization at startup. `python scripts/seed.py` inserts the demo documents afterward.

## Collections

### `users`

```json
{
  "_id": "staff-asha",
  "name": "Asha Iyer",
  "email": "asha.iyer@example.com",
  "role": "staff",
  "manager_id": "manager-west",
  "monthly_limit_paise": 800000,
  "active": true
}
```

Allowed roles: `staff`, `manager`, `finance`.

### `claims`

```json
{
  "_id": "ObjectId",
  "claimant_id": "staff-asha",
  "approver_id": "manager-west",
  "merchant": "Meru Cabs",
  "category": "Taxi",
  "amount_paise": 21400,
  "currency": "INR",
  "expense_date": "2026-09-12T00:00:00Z",
  "receipt_no": "4471",
  "raw_text": "Original receipt text",
  "source": "text",
  "fingerprint": "meru cabs|21400|2026-09-12",
  "duplicate_of": null,
  "duplicate_reason": null,
  "duplicate_ack_note": null,
  "status": "submitted",
  "status_history": [
    {
      "who": "staff-asha",
      "from": "draft",
      "to": "submitted",
      "when": "2026-09-19T10:00:00Z",
      "note": null
    }
  ],
  "created_at": "2026-09-19T10:00:00Z",
  "paid_at": null,
  "payout_ref": null
}
```

Allowed categories: `Travel`, `Meals`, `Supplies`, `Taxi`, `Lodging`, `Other`.

Allowed statuses: `draft`, `submitted`, `approved`, `rejected`, `paid`.

## Indexes

Created by `app.db.ensure_indexes()`:

```javascript
db.claims.createIndex({ status: 1 }, { name: "claims_status" });
db.claims.createIndex(
  { claimant_id: 1, expense_date: 1 },
  { name: "claims_claimant_date" },
);
db.claims.createIndex(
  { fingerprint: 1 },
  {
    name: "claims_strong_fingerprint",
    unique: true,
    partialFilterExpression: {
      status: { $in: ["draft", "submitted", "approved", "paid"] },
      fingerprint: { $type: "string", $gt: "" },
    },
  },
);
```

The fingerprint index is a database-level final guard against strong duplicates. Rejected claims are excluded so a corrected/resubmitted expense is not permanently blocked by its rejected predecessor.

## Setup

Initialize the database and collections:

```text
copy .env.example .env
python scripts/init_db.py
python scripts/seed.py
```

For Atlas, set `MONGODB_URI` to the `mongodb+srv://` connection string and run the same initialization and seed commands from a trusted environment. No SQL table-creation script is required because MongoDB uses collections.
