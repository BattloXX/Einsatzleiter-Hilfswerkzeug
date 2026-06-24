"""Retention der Wetterstations-Zeitreihe – täglicher Background-Loop.

Löscht Messwerte aus der separaten Wetter-DB, die älter als
``settings.WEATHER_READING_RETENTION_DAYS`` sind. Das hält die Zeitreihe schlank
und verhindert unbegrenztes Wachstum.

Schonend für den Betrieb (Einsatz hat Vorrang):
- Läuft einmal täglich nachts (Standard 03:30 Europe/Vienna).
- Löscht in Chunks (je Commit), um lange Sperren zu vermeiden.
- Arbeitet ausschließlich auf der Wetter-DB (eigener Pool) – die operative DB
  wird nicht berührt.
"""
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.db_weather import get_weather_session, weather_db_enabled

logger = logging.getLogger("einsatzleiter.weather")

_CHUNK_SIZE = 5000
_PURGE_HOUR = 3
_PURGE_MINUTE = 30

try:
    from zoneinfo import ZoneInfo
    _VIENNA_TZ = ZoneInfo("Europe/Vienna")
except Exception:  # pragma: no cover
    _VIENNA_TZ = UTC


def purge_old_readings(retention_days: int | None = None, chunk_size: int = _CHUNK_SIZE) -> int:
    """Löscht Messwerte älter als retention_days in Chunks. Gibt die Anzahl zurück.

    No-op (0), wenn keine Wetter-DB konfiguriert ist.
    """
    if not weather_db_enabled():
        return 0

    days = retention_days if retention_days is not None else settings.WEATHER_READING_RETENTION_DAYS
    if days <= 0:
        return 0

    from app.models.weather import WeatherReading

    cutoff = datetime.now(UTC) - timedelta(days=days)
    total = 0
    session = get_weather_session()
    try:
        while True:
            ids = [
                row[0]
                for row in session.query(WeatherReading.id)
                .filter(WeatherReading.ts < cutoff)
                .limit(chunk_size)
                .all()
            ]
            if not ids:
                break
            session.query(WeatherReading).filter(
                WeatherReading.id.in_(ids)
            ).delete(synchronize_session=False)
            session.commit()
            total += len(ids)
            if len(ids) < chunk_size:
                break
    except Exception:
        session.rollback()
        logger.exception("Wetter-Retention: Löschen fehlgeschlagen")
        raise
    finally:
        session.close()

    if total:
        logger.info("Wetter-Retention: %d alte Messwerte gelöscht (älter als %d Tage).", total, days)
    return total


def purge_old_abfluss_readings(retention_days: int | None = None, chunk_size: int = _CHUNK_SIZE) -> int:
    """Löscht Pegelmessungen älter als retention_days in Chunks. Gibt die Anzahl zurück."""
    if not weather_db_enabled():
        return 0

    days = retention_days if retention_days is not None else settings.WEATHER_READING_RETENTION_DAYS
    if days <= 0:
        return 0

    from app.models.weather import AbflussReading

    cutoff = datetime.now(UTC) - timedelta(days=days)
    total = 0
    session = get_weather_session()
    try:
        while True:
            ids = [
                row[0]
                for row in session.query(AbflussReading.id)
                .filter(AbflussReading.ts < cutoff)
                .limit(chunk_size)
                .all()
            ]
            if not ids:
                break
            session.query(AbflussReading).filter(
                AbflussReading.id.in_(ids)
            ).delete(synchronize_session=False)
            session.commit()
            total += len(ids)
            if len(ids) < chunk_size:
                break
    except Exception:
        session.rollback()
        logger.exception("Wetter-Retention Abfluss: Löschen fehlgeschlagen")
        raise
    finally:
        session.close()

    if total:
        logger.info("Wetter-Retention Abfluss: %d alte Pegelmessungen gelöscht (älter als %d Tage).", total, days)
    return total


def _seconds_until_next(hour: int, minute: int) -> float:
    """Sekunden bis zum nächsten Zeitpunkt hour:minute in Europe/Vienna."""
    now = datetime.now(_VIENNA_TZ)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def weather_retention_loop() -> None:
    """Täglicher Loop: wartet bis 03:30 und löscht dann überfällige Messwerte."""
    if not weather_db_enabled():
        logger.info("Wetter-Retention deaktiviert (keine Wetter-DB konfiguriert).")
        return
    while True:
        await asyncio.sleep(_seconds_until_next(_PURGE_HOUR, _PURGE_MINUTE))
        try:
            await asyncio.to_thread(purge_old_readings)
            await asyncio.to_thread(purge_old_abfluss_readings)
        except Exception:
            logger.exception("Fehler im Wetter-Retention-Loop")
