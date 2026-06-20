"""UAS-Modul Router – PR 0: Guard-Dependency + Einstiegsseite.

Alle UAS-Routen (PR 0–8) hängen require_uas_enabled an. Bei nicht-aktivem
Modul → HTTP 404 (Existenz nicht leaken), konsistent für Seiten und API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.permissions import require_role
from app.core.templating import templates
from app.db import get_db
from app.models.user import User

router = APIRouter(prefix="/uas", tags=["uas"])


def require_uas_enabled(request: Request) -> None:
    """Guard-Dependency: wirft HTTP 404 wenn UAS-Modul nicht effektiv aktiv.

    Liest request.state.uas_module_enabled (gesetzt von _resolve_current_org).
    Alle UAS-Routen (PR 0-8) MÜSSEN diese Dependency einbinden.
    """
    if not getattr(request.state, "uas_module_enabled", False):
        raise HTTPException(status_code=404, detail="Nicht gefunden")


@router.get("/", response_class=HTMLResponse)
def uas_index(
    request: Request,
    db=Depends(get_db),
    user: User = Depends(require_role("recorder")),
    _guard: None = Depends(require_uas_enabled),
):
    """UAS-Modul Startseite (Platzhalter bis PR 3)."""
    return templates.TemplateResponse(request, "uas/index.html", {"user": user})
