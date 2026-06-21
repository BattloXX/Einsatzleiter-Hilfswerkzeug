"""Automatische Geräteverleih-Erinnerungs-SMS – Background-Loop.

Prüft alle 60 Sekunden ob fällige Erinnerungen vorhanden sind:
- status=ausgeliehen
- erinnerung_geplant_at <= now
- erinnerung_gesendet_at is None
- telefon not null
"""
import asyncio
import logging
from datetime import UTC, datetime

from app.core.tenant import set_tenant_context
from app.db import SessionLocal
from app.models.verleih import VerleihAusleihe, VerleihStatus
from app.services import verleih_service as svc

logger = logging.getLogger("einsatzleiter.verleih_erinnerung")


async def verleih_erinnerung_loop() -> None:
    while True:
        await asyncio.sleep(60)
        try:
            await _check_fällige_erinnerungen()
        except Exception:
            logger.exception("Fehler im Verleih-Erinnerungs-Loop")


async def _check_fällige_erinnerungen() -> None:
    from app.services.sms_service import send_sms

    with SessionLocal() as db:
        set_tenant_context(db, None)  # system_admin-Modus: alle Orgs
        now = datetime.now(UTC)
        faellige = (
            db.query(VerleihAusleihe)
            .filter(
                VerleihAusleihe.status == VerleihStatus.ausgeliehen,
                VerleihAusleihe.erinnerung_geplant_at <= now,
                VerleihAusleihe.erinnerung_gesendet_at.is_(None),
                VerleihAusleihe.telefon.isnot(None),
            )
            .all()
        )

        for ausleihe in faellige:
            try:
                text = svc.get_sms_erinnerung_text(db, ausleihe.org_id, ausleihe)
                ok = await send_sms(ausleihe.org_id, ausleihe.telefon, text)
                if ok:
                    ausleihe.erinnerung_gesendet_at = datetime.now(UTC)
                    db.commit()
                    logger.info(
                        "Erinnerungs-SMS gesendet: Ausleihe %s, Org %s",
                        ausleihe.id, ausleihe.org_id,
                    )
                else:
                    logger.warning("Erinnerungs-SMS fehlgeschlagen: Ausleihe %s", ausleihe.id)
            except Exception:
                logger.exception("Fehler bei Erinnerungs-SMS für Ausleihe %s", ausleihe.id)
