# Expense Claims

An accountant-style expense claims application for staff, managers, and finance teams. Staff paste receipt text, review the extracted claim, submit it to an assigned manager, and track payment. Managers approve or reject their team's claims. Finance monitors monthly spend, duplicate risk, limits, and emulated payouts.

Live URL: _add deployment URL here_.

Detailed project summary, workflow, ER diagram, and testcase catalog: [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md). MongoDB collection definitions and indexes: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).

## Run locally

1. Install Python 3.11+ and MongoDB 6+ or create a MongoDB Atlas cluster.
2. `python -m venv .venv`
3. `.venv\\Scripts\\activate` on Windows, or `source .venv/bin/activate` on macOS/Linux.
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure the variables below.
6. Initialize the MongoDB collections and indexes: `python scripts/init_db.py`
7. Add demo users and claims: `python scripts/seed.py`
8. `uvicorn app.main:app --reload`

Open `http://127.0.0.1:8000`. Demo authentication deliberately lists seeded users without passwords so reviewers can switch roles quickly. Real deployment would replace it with SSO or password authentication, MFA, and account recovery.

The seeded sign-in accounts use `Welcome@123` for employees and `Admin@12345` for the `admin` account. Change these credentials before sharing a deployment. The batch receipt workflow accepts PDF, JPG, JPEG, and PNG files. PDF text extraction works after the Python dependencies install; image OCR also requires the Tesseract executable installed and available on `PATH` on Windows.

## Configuration

Configuration is environment-only. Do not commit `.env`, MongoDB passwords, session secrets, or API keys.

| Variable       | Required | Example                        | Purpose                                                                         |
| -------------- | -------- | ------------------------------ | ------------------------------------------------------------------------------- |
| `MONGODB_URI`  | Yes      | `mongodb://localhost:27017`    | MongoDB connection string. Atlas uses `mongodb+srv://...`.                      |
| `MONGODB_DB`   | Yes      | `expense_claims`               | Database name.                                                                  |
| `SECRET_KEY`   | Yes      | `generate-a-long-random-value` | Signs the session cookie. Use a different value per environment.                |
| `LLM_PROVIDER` | No       | `gemini`                       | Enables Google AI Studio Gemini extraction. Leave empty for local-only parsing. |
| `LLM_API_KEY`  | No       | _not committed_                | Google AI Studio API key. Leave empty to use the deterministic parser.          |
| `APP_ENV`      | Yes      | `development` or `production`  | Enables secure cookies in production.                                           |

Generate a local session secret with Python:

```text
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

For MongoDB Atlas, create a database user, copy its connection string, replace the password placeholder, and set `MONGODB_URI` in `.env` or the host dashboard. For Google AI Studio, create an API key, set `LLM_PROVIDER=gemini`, and set `LLM_API_KEY` privately. Never send the password or API key through chat. Gemini failures automatically use the local parser.

## Architecture

```text
Browser + HTMX-ready forms -> FastAPI routes -> services -> MongoDB
                                  |              |-- claims state machine
                                  |              |-- duplicate detector
                                  |              |-- receipt parser
                                  |              |-- reports and payouts
                                  `-> Jinja templates + ledger CSS
```

## Decisions and assumptions

- Stack is FastAPI, Jinja2, MongoDB/PyMongo, Pydantic v2, rapidfuzz, signed sessions, and pytest. No frontend build step.
- Money is integer paise and currency is INR only; this avoids floating-point errors.
- Expense month means the month of `expense_date`, not creation or payment month.
- Monthly limits warn at 90% and flag over-limit claims; managers still decide.
- Duplicate checks exclude rejected claims. Exact merchant/amount/date and receipt-number matches block. Same amount plus merchant similarity of 85 within 30 days blocks but permits a mandatory exception note. Same claimant/date within 2% warns.
- Top-level managers use the seeded Head of Operations assumption as last-resort approver. The demo seed keeps that senior reviewer visible for the review workflow.
- Receipts older than 90 days, future dates, non-positive amounts, and amounts above the cap are rejected. Parser output is always shown for correction before submission.
- Payments are emulated with a generated payout reference. Payment updates filter on `status=approved` so concurrent clicks cannot pay twice.
- AI tools used: GitHub Copilot for scaffolding and tests. Add other tools here honestly if used.

## Deployment

Create a free MongoDB Atlas cluster, create a strong database password, and allow `0.0.0.0/0` because Render free services do not have a fixed outbound IP. This is the practical trade-off for the free tier; use private networking or an allowlist in a production setup. Add the environment variables from `render.yaml` in the Render dashboard and deploy from GitHub. The free service sleeps, so its first request may take 30 to 50 seconds.

The application also runs collection/index initialization at startup. After deployment, run `python scripts/init_db.py` once using a one-off shell/job with the same environment variables, then run `python scripts/seed.py` once for demo data. Confirm `/healthz` returns `{"status":"ok"}`.

## Testing

```text
.venv\\Scripts\\python.exe -m pytest -q
```

The suite uses mongomock and does not require a live MongoDB instance. It covers the state machine, terminal paid claims, approval authorization, double-pay protection, all duplicate layers, rejected-claim exclusion, messy receipt parsing, and date/amount validation.

## Limitations and next week

The demo has no real OCR or image persistence, no SSO, no category caps, email notifications, audit export, S3 receipt storage, embeddings duplicate matching, line items, or mobile PWA. With another week I would add those in that order based on user value and operational risk.
