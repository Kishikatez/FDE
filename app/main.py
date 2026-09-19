"""FastAPI application entry point."""

from fastapi import FastAPI

from app.db import get_database

app = FastAPI(title="Expense Claims")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report application and MongoDB connectivity."""

    get_database().command("ping")
    return {"status": "ok"}
