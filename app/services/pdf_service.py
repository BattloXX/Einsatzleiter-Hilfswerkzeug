"""PDF generation via WeasyPrint."""
import base64
import io
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from app.config import settings
from app.core.templating import templates
from app.core.tenant import set_tenant_context
from app.db import SessionLocal
from app.models.incident import Incident
from app.models.master import FireDept


def _media_b64_uri(media) -> str:
    """Returns a base64 data URI for an image media object, or '' if unavailable."""
    if media.kind != "image":
        return ""
    path = Path(settings.MEDIA_STORAGE_DIR) / media.storage_path
    if not path.exists():
        return ""
    data = path.read_bytes()
    return f"data:{media.mime_type};base64,{base64.b64encode(data).decode()}"


def _media_file_exists(media) -> bool:
    path = Path(settings.MEDIA_STORAGE_DIR) / media.storage_path
    return path.exists()


def _resolve_primary_org(incident: Incident) -> FireDept | None:
    """Lädt die Primary-Org für die Zeitzonen-Konvertierung in den Filtern."""
    if not incident.primary_org_id:
        return None
    db = SessionLocal()
    set_tenant_context(db, None)
    try:
        return db.get(FireDept, incident.primary_org_id)
    finally:
        db.close()


def _load_incident_teilnahmen(incident_id: int) -> list:
    """Lädt Teilnahmen für einen Einsatz ohne Tenant-Filter (PDF-Kontext)."""
    from app.models.teilnahme import Teilnahme
    db = SessionLocal()
    set_tenant_context(db, None)
    try:
        return db.query(Teilnahme).filter(
            Teilnahme.bezug_typ == "einsatz",
            Teilnahme.bezug_id == incident_id,
        ).execution_options(include_all_tenants=True).order_by(Teilnahme.hinzugefuegt_am).all()
    finally:
        db.close()


def render_incident_pdf(incident: Incident, base_url: str = "") -> bytes:
    template = templates.env.get_template("pdf/incident_report.html")
    primary_org = _resolve_primary_org(incident)
    pseudo_user = SimpleNamespace(org=primary_org)
    teilnahmen = _load_incident_teilnahmen(incident.id)

    html_str = template.render(
        incident=incident,
        teilnahmen=teilnahmen,
        now=datetime.now(UTC),
        base_url=base_url,
        user=pseudo_user,
        media_b64=_media_b64_uri,
        media_exists=_media_file_exists,
    )
    from weasyprint import HTML  # noqa: PLC0415 – lazy: GTK not available on Windows
    buf = io.BytesIO()
    HTML(string=html_str, base_url=base_url or ".").write_pdf(buf)
    return buf.getvalue()


def render_troop_pdf(troop, incident: Incident, base_url: str = "") -> bytes:
    """Einzelexport eines Atemschutztrupps als vollständiges A4-PDF."""
    template = templates.env.get_template("pdf/troop_protocol.html")
    primary_org = _resolve_primary_org(incident)
    pseudo_user = SimpleNamespace(org=primary_org)

    html_str = template.render(
        troop=troop,
        incident=incident,
        now=datetime.now(UTC),
        base_url=base_url,
        user=pseudo_user,
    )
    from weasyprint import HTML  # noqa: PLC0415 – lazy: GTK not available on Windows
    buf = io.BytesIO()
    HTML(string=html_str, base_url=base_url or ".").write_pdf(buf)
    return buf.getvalue()


def render_teilnahme_pdf(
    teilnahmen: list,
    bezug_typ: str,
    titel: str,
    beginn,
    ort: str | None,
    user,
    base_url: str = "",
) -> bytes:
    """Teilnehmerliste als A4-PDF (WeasyPrint)."""
    template = templates.env.get_template("pdf/teilnahme_report.html")
    html_str = template.render(
        teilnahmen=teilnahmen,
        bezug_typ=bezug_typ,
        titel=titel,
        beginn=beginn,
        ort=ort,
        user=user,
        now=datetime.now(UTC),
        base_url=base_url,
    )
    from weasyprint import HTML  # noqa: PLC0415 – lazy: GTK not available on Windows
    buf = io.BytesIO()
    HTML(string=html_str, base_url=base_url or ".").write_pdf(buf)
    return buf.getvalue()
