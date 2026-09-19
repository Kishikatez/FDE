"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.config import get_settings
from app.db import ensure_indexes, get_database
from app.routes.web import router

app = FastAPI(title="Expense Claims")
settings = get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=settings.app_env == "production",
    same_site="lax",
)
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def initialize_database() -> None:
    """Create MongoDB collections and indexes when the service starts."""

    ensure_indexes()


@app.exception_handler(PermissionError)
async def permission_error(request: Request, exc: PermissionError) -> HTMLResponse:
    """Return a friendly response without exposing internal details."""

    return HTMLResponse(f"<h1>Access denied</h1><p>{exc}</p>", status_code=403)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Report application and MongoDB connectivity."""

    get_database().command("ping")
    return {"status": "ok"}
