"""Öffentliche Seiten (Startseite, Impressum, About, Kontakt) + Startseiten-CMS.

Die Startseite selbst wird von ``ui_incident.index`` für nicht angemeldete Nutzer
gerendert. Hier liegen die übrigen öffentlichen Routen sowie die nur für
Systemadmins zugänglichen Pflege-Endpunkte.
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.core.permissions import require_system_admin
from app.core.templating import templates
from app.db import get_db
from app.models.user import User
from app.services import landing as landing_service
from app.services.mail_service import send_contact_message

logger = logging.getLogger("einsatzleiter.public")

router = APIRouter()

ALLOWED_IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMG_BYTES = 4 * 1024 * 1024  # 4 MB


# ── Öffentliche Seiten ────────────────────────────────────────────────────────

@router.get("/impressum", response_class=HTMLResponse)
async def impressum(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(request, "public/impressum.html", {
        "user": getattr(request.state, "user", None),
        "c": landing_service.get_landing_content(db),
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, db=Depends(get_db)):
    return templates.TemplateResponse(request, "public/about.html", {
        "user": getattr(request.state, "user", None),
        "c": landing_service.get_landing_content(db),
    })


@router.post("/kontakt")
async def contact_submit(
    request: Request, db=Depends(get_db),
    name: str = Form(""), email: str = Form(""), message: str = Form(""),
    website: str = Form(""),  # Honeypot – muss leer bleiben
):
    # Bots füllen oft alle Felder inkl. verstecktem Honeypot aus → still verwerfen.
    if website.strip():
        return RedirectResponse("/?kontakt=ok#kontakt", status_code=303)
    if not name.strip() or not email.strip() or not message.strip():
        return RedirectResponse("/?kontakt=fehler#kontakt", status_code=303)
    try:
        await send_contact_message(
            name=name.strip(), reply_email=email.strip(), message=message.strip(), db=db,
        )
    except Exception:
        logger.exception("Kontaktformular: Versand fehlgeschlagen")
        return RedirectResponse("/?kontakt=fehler#kontakt", status_code=303)
    return RedirectResponse("/?kontakt=ok#kontakt", status_code=303)


@router.get("/startseite/bild/{slug}")
async def landing_image(slug: str, db=Depends(get_db)):
    path = landing_service.image_file_path(db, slug)
    if not path:
        raise HTTPException(404, "Bild nicht gefunden")
    return FileResponse(path)


# ── CMS (nur system_admin) ────────────────────────────────────────────────────

@router.get("/admin/startseite", response_class=HTMLResponse)
async def landing_edit(request: Request, db=Depends(get_db),
                       user: User = Depends(require_system_admin)):
    return templates.TemplateResponse(request, "admin/landing_edit.html", {
        "user": user,
        "c": landing_service.get_landing_content(db),
        "text_fields": landing_service.TEXT_FIELDS,
        "image_slugs": landing_service.IMAGE_SLUGS,
        "saved": request.query_params.get("saved"),
    })


@router.post("/admin/startseite")
async def landing_save(request: Request, db=Depends(get_db),
                       user: User = Depends(require_system_admin)):
    form = await request.form()
    for key in landing_service.TEXT_DEFAULTS:
        if key in form:
            landing_service.set_setting(
                db, landing_service.SETTINGS_PREFIX + key, str(form[key]).strip(), user.id,
            )
    db.commit()
    return RedirectResponse("/admin/startseite?saved=texte", status_code=303)


@router.post("/admin/startseite/bild")
async def landing_save_image(request: Request, db=Depends(get_db),
                             user: User = Depends(require_system_admin),
                             slug: str = Form(...), image: UploadFile = File(...)):
    if slug not in landing_service.IMAGE_SLUGS:
        raise HTTPException(400, "Unbekannter Bild-Slot")
    ext = Path(image.filename or "").suffix.lower()
    if ext not in ALLOWED_IMG_EXTS:
        raise HTTPException(400, "Format nicht erlaubt (erlaubt: PNG, JPG, WEBP)")
    data = await image.read()
    if not data:
        raise HTTPException(400, "Leere Datei")
    if len(data) > MAX_IMG_BYTES:
        raise HTTPException(400, f"Datei zu groß (max {MAX_IMG_BYTES // (1024 * 1024)} MB)")

    landing_service.LANDING_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}-{uuid.uuid4().hex[:8]}{ext}"
    (landing_service.LANDING_DIR / filename).write_bytes(data)
    landing_service.store_image(db, slug, filename, user.id)
    db.commit()
    return RedirectResponse("/admin/startseite?saved=bild", status_code=303)
