"""Create the MongoDB database collections and indexes."""

import sys
from pathlib import Path

# Keep `python scripts/init_db.py` convenient as well as `python -m scripts.init_db`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import ensure_indexes, get_settings


def main() -> None:
    """Initialize the configured database without inserting demo records."""

    ensure_indexes()
    settings = get_settings()
    print(f"Database initialized: {settings.mongodb_db}")
    print("Collections: users, claims")
    print("Indexes: users_email_unique, claims_status, claims_claimant_date, claims_strong_fingerprint")


if __name__ == "__main__":
    main()