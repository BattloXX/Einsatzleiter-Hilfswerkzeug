"""Retention der GPS-Positionshistorie – täglicher Background-Loop.

Löscht Einträge aus vehicle_position, die älter als
``settings.VEHICLE_POSITION_RETENTION_DAYS`` sind, um unbegrenztes
Tabellenwachstum (alle 3 Minuten pro Gerät) zu verhindern.

Schonend für den Betrieb (Einsatz hat Vorrang):
- Läuft einmal täglich nachts (03:45 Europe/Vienna).
- Löscht in Chunks (je Commit), um lange Tabellensperren zu vermeiden.
"""
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.db import SessionLocal

logger = logging.getLogger("einsatzleiter.vehicle_position")

_CHUNK_SIZE = 5000
_PURGE_HOUR = 3
_PURGE_MINUTE = 45

try:
    from zoneinfo import ZoneInfo
    _VIENNA_TZ = ZoneInfo("Europe/Vienna")
except Exception:  # pragma: no cover
    _VIENNA_TZ = UTC


def purge_old_vehicle_positions(retention_days: int | None = None, chunk_size: int = _CHUNK_SIZE) -> int:
    """Löscht GPS-Punkte älter als retention_days in Chunks. Gibt die Anzahl zurück."""
    days = retention_days if retention_days is not None else settings.VEHICLE_POSITION_RETENTION_DAYS
    if days <= 0:
        return 0

    from app.models.major_incident import VehiclePosition

    cutoff = datetime.now(UTC) - timedelta(days=days)
    total = 0
    db = SessionLocal()
    try:
        while True:
            ids = [
                row[0]
                for row in db.query(VehiclePosition.id)
                .filter(VehiclePosition.received_at < cutoff)
                .limit(chunk_size)
                .all()
            ]
            if not ids:
                break
            db.query(VehiclePosition).filter(
                VehiclePosition.id.in_(ids)
            ).delete(synchronize_session=False)
            db.commit()
            total += len(ids)
            if len(ids) < chunk_size:
                break
    except Exception:
        db.rollback()
        logger.exception("VehiclePosition-Retention: Löschen fehlgeschlagen")
        raise
    finally:
        db.close()

    if total:
        logger.info(
            "VehiclePosition-Retention: %d alte GPS-Punkte gelöscht (älter als %d Tage).",
            total, days,
        )
    return total


def _seconds_until_next(hour: int, minute: int) -> float:
    """Sekunden bis zum nächsten Zeitpunkt hour:minute in Europe/Vienna."""
    now = datetime.now(_VIENNA_TZ)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def vehicle_position_retention_loop() -> None:
    """Täglicher Loop: wartet bis 03:45 und löscht überfällige GPS-Punkte."""
    while True:
        await asyncio.sleep(_seconds_until_next(_PURGE_HOUR, _PURGE_MINUTE))
        try:
            await asyncio.to_thread(purge_old_vehicle_positions)
        except Exception:
            logger.exception("Fehler im VehiclePosition-Retention-Loop")
