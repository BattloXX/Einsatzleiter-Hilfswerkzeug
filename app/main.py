"""FastAPI application – Einsatzleiter-Hilfswerkzeug (Multi-Org) v2.0.0."""
import logging
import secrets as _secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, validate_startup_secrets
from app.db import SessionLocal, engine
from app.core.security import unsign_session
from app.models.user import User

from app.routers import auth, api_v1, ws
from app.routers import (
    ui_incident,
    ui_breathing,
    ui_archive,
    ui_admin,
    ui_media,
    ui_stats,
    ui_push,
    ui_settings,
    ui_password_reset,
)

logger = logging.getLogger("einsatzleiter")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup-Validierung der kritischen Konfiguration
    errors = validate_startup_secrets()
    if errors and not settings.DEBUG:
        for err in errors:
            logger.critical("Konfigurationsfehler: %s", err)
        raise RuntimeError(
            "Fataler Konfigurationsfehler beim Start: "
            + "; ".join(errors)
            + ". Setze SECRET_KEY in der .env auf einen langen zufälligen String."
        )
    elif errors:
        for err in errors:
            logger.warning("Konfigurations-Warnung (DEBUG=True): %s", err)

    # Bootstrap admin on first start
    _bootstrap_admin()
    yield


def _bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        from app.models.user import User as U
        existing = db.query(U).first()
        if existing:
            return
        from app.seed_data import seed
        seed(db)
        from app.cli import create_admin

        password = settings.BOOTSTRAP_ADMIN_PASSWORD
        generated = False
        if not password:
            password = _secrets.token_urlsafe(18)
            generated = True

        create_admin(settings.BOOTSTRAP_ADMIN_USER, password)

        if generated:
            # Einmalige Ausgabe — Admin muss das Passwort sofort notieren
            logger.warning("=" * 70)
            logger.warning("BOOTSTRAP-ADMIN ANGELEGT — diesen Block einmalig notieren:")
            logger.warning("  Benutzer:  %s", settings.BOOTSTRAP_ADMIN_USER)
            logger.warning("  Passwort:  %s", password)
            logger.warning("Beim nächsten Login bitte Passwort ändern.")
            logger.warning("=" * 70)
    except Exception:
        # Another worker may have seeded concurrently — safe to ignore
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title="Einsatzleiter-Hilfswerkzeug",
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Session middleware – inject request.state.user
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    token = request.cookies.get("session")
    request.state.user = None
    if token:
        user_id = unsign_session(token)
        if user_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id, User.active == True).first()  # noqa: E712
                request.state.user = user
            finally:
                db.close()
    return await call_next(request)


# Security headers middleware (Phase 7)
try:
    from app.middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
except ImportError:  # falls Modul noch nicht vorhanden
    pass

# CSRF (Phase 7)
try:
    from app.middleware.csrf import CSRFMiddleware
    app.add_middleware(CSRFMiddleware)
except ImportError:
    pass

# Rate-Limit via slowapi (Phase 7) — wenn nicht installiert, einfach überspringen.
try:
    from slowapi import Limiter  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.middleware import SlowAPIMiddleware  # type: ignore
    from starlette.responses import JSONResponse

    # Default-Limit für alle Requests; einzelne Endpoints (login, password-reset)
    # können engere Limits per Decorator setzen
    limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _ratelimit_handler(request, exc):  # type: ignore[override]
        return JSONResponse(
            {"detail": "Zu viele Versuche. Bitte später erneut probieren."},
            status_code=429,
        )
except ImportError:
    limiter = None  # type: ignore


# Routers
app.include_router(auth.router)
app.include_router(ui_password_reset.router)
app.include_router(api_v1.router)
app.include_router(ws.router)
app.include_router(ui_incident.router)
app.include_router(ui_media.router)
app.include_router(ui_breathing.router)
app.include_router(ui_archive.router)
app.include_router(ui_admin.router)
app.include_router(ui_stats.router)
app.include_router(ui_push.router)
app.include_router(ui_settings.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse("/static/img/favicon.ico")
