"""Kachelmann Wetter (Plus-API) client — premium primary weather source.

Aktiv nur wenn ein API-Key gepflegt ist (Systemeinstellung `kachelmann_api_key`
oder ENV `KACHELMANN_API_KEY`). Liefert Ist-Werte und Vorhersage in denselben
Dataclasses wie `weather_service` (CurrentWeather, ForecastResult), damit Router
und Templates unverändert bleiben. Quelle wird mit `source="kachelmann"` markiert.

Robustheit: Alle HTTP-/Parsing-Fehler werden geloggt und als None zurückgegeben —
weather_service fällt dann still auf ZAMG/GeoSphere zurück. Niemals Exception nach
außen.

Hinweis: Die exakten Feldnamen/Einheiten der Kachelmann-Antwort sind erst mit
gültigem Key endgültig verifizierbar. Das Parsing arbeitet daher mit Feld-Aliasen
und einer Wind-Einheiten-Heuristik (siehe `_norm_wind_ms`). Bei Abweichung nur die
Alias-Listen bzw. die Heuristik anpassen.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.weather_service import (
    CurrentWeather,
    ForecastHorizon,
    ForecastResult,
    _parse_timestamps,
    _safe_float,
)

logger = logging.getLogger("einsatzleiter.weather")

_SOURCE = "kachelmann"

# ── API-Key-Lookup (Systemeinstellung → ENV), kurz gecacht ────────────────────

_KEY_CACHE_TTL = 60.0   # s
_key_cache: tuple[str | None, float] | None = None


def _get_api_key() -> str | None:
    """Liest `kachelmann_api_key` aus SystemSettings, Fallback ENV. 60 s gecacht.

    Muster analog `ai_service._get_ai_cfg()`.
    """
    global _key_cache
    now = time.monotonic()
    if _key_cache is not None and now - _key_cache[1] < _KEY_CACHE_TTL:
        return _key_cache[0]

    value: str | None = None
    from_db = False
    try:
        from app.core.tenant import set_tenant_context
        from app.db import SessionLocal
        from app.models.master import SystemSettings as _SS
        db = SessionLocal()
        set_tenant_context(db, None)
        try:
            row = db.get(_SS, "kachelmann_api_key")
            value = (row.value or "").strip() if row and row.value else None
            from_db = value is not None
        finally:
            db.close()
    except Exception as exc:
        # DB nicht erreichbar o.ä. — nicht fatal, ENV-Fallback greift.
        logger.warning("Kachelmann-Key konnte nicht aus den Systemeinstellungen gelesen werden: %s", exc)
        value = None

    if not value:
        value = (settings.KACHELMANN_API_KEY or "").strip() or None
        if value:
            logger.info("Kachelmann-Key aus Umgebungsvariable KACHELMANN_API_KEY verwendet.")

    if value is None:
        logger.debug("Kein Kachelmann-API-Key gesetzt – Wetterdaten kommen von ZAMG/GeoSphere.")
    elif from_db:
        logger.debug("Kachelmann-Key aus Systemeinstellungen geladen.")

    _key_cache = (value, now)
    return value


def reset_key_cache() -> None:
    """Erzwingt erneutes Einlesen des Keys (z.B. nach Speichern in den Settings)."""
    global _key_cache
    _key_cache = None


def is_configured() -> bool:
    """True wenn ein Kachelmann-API-Key vorhanden ist."""
    return _get_api_key() is not None


# ── HTTP-Client ───────────────────────────────────────────────────────────────

async def _get(path: str, params: dict | None = None) -> dict | None:
    """Single GET gegen die Kachelmann-API. Gibt JSON-dict oder None zurück."""
    api_key = _get_api_key()
    if not api_key:
        return None
    url = f"{settings.KACHELMANN_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(
            headers={
                "X-API-Key": api_key,
                "User-Agent": "Einsatzleiter-Hilfswerkzeug/2.x (weather)",
                "Accept": "application/json",
            },
            timeout=settings.WEATHER_HTTP_TIMEOUT,
        ) as client:
            resp = await client.get(url, params=dict(params or {}, units="metric"))
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else None
    except httpx.TimeoutException:
        logger.warning("Kachelmann Timeout: %s", path)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status in (401, 403):
            logger.warning(
                "Kachelmann HTTP %s bei %s – API-Key ungültig oder Abo deckt den Endpunkt "
                "nicht ab. Es wird auf ZAMG/GeoSphere zurückgegriffen.", status, path,
            )
        elif status == 429:
            logger.warning("Kachelmann HTTP 429 bei %s – Rate-Limit erreicht.", path)
        else:
            logger.warning("Kachelmann HTTP %s: %s", status, path)
    except Exception as exc:
        logger.warning("Kachelmann Fehler: %s (%s)", exc, path)
    return None


# ── Parsing-Helfer ────────────────────────────────────────────────────────────

def _pick(d: dict, *keys: str) -> Any:
    """Erstes vorhandenes (nicht-None) Feld aus einer Alias-Liste."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _norm_wind_ms(val: float | None) -> float | None:
    """Normalisiert Windgeschwindigkeit auf m/s.

    Heuristik: Werte > 40 werden als km/h interpretiert (40 m/s ≈ BF13, in
    Mitteleuropa praktisch nie erreicht) und nach m/s umgerechnet. Bei `units=metric`
    liefert Kachelmann i.d.R. bereits m/s — dann bleibt der Wert unverändert.
    """
    if val is None:
        return None
    return val / 3.6 if val > 40.0 else val


# ── Ist-Werte ─────────────────────────────────────────────────────────────────

async def fetch_current(lat: float, lng: float) -> CurrentWeather | None:
    """Aktuelle Bedingungen von Kachelmann (`/current/{lat}/{lon}`)."""
    data = await _get(f"/current/{lat}/{lng}")
    if not data:
        return None
    return _parse_current(data)


def _parse_current(data: dict) -> CurrentWeather | None:
    # Nutzdaten können verschachtelt sein (z.B. {"data": {...}})
    d = data.get("data") if isinstance(data.get("data"), dict) else data
    if not isinstance(d, dict):
        return None

    temp = _safe_float(_pick(d, "temperature", "temp", "airTemperature", "t2m"))
    hum = _safe_float(_pick(d, "relativeHumidity", "humidity", "rh", "rh2m"))
    wind = _norm_wind_ms(_safe_float(_pick(d, "windSpeed", "wind", "ff")))
    gust = _norm_wind_ms(_safe_float(_pick(d, "windGust", "gust", "windGustSpeed", "fx")))
    wdir = _safe_float(_pick(d, "windDirection", "windDir", "dd"))
    prec = _safe_float(_pick(d, "precipitation", "prec1h", "precip", "rr"))

    if temp is None and wind is None and prec is None:
        # Antwortstruktur passt nicht → Fallback auslösen
        return None

    return CurrentWeather(
        temperature_c=temp,
        humidity_pct=hum,
        wind_speed_ms=wind,
        gust_speed_ms=gust,
        wind_direction_deg=wdir,
        precipitation_1h_mm=prec,
        source=_SOURCE,
    )


# ── Vorhersage ────────────────────────────────────────────────────────────────

async def fetch_forecast(
    lat: float, lng: float, horizons: tuple[int, ...] = (6, 12, 24)
) -> ForecastResult | None:
    """Mehrhorizont-Vorhersage von Kachelmann (`/forecast/3days/{lat}/{lon}`)."""
    data = await _get(f"/forecast/3days/{lat}/{lng}")
    if not data:
        return None
    return _parse_forecast(data, horizons)


def _extract_hourly(data: dict) -> list[dict]:
    """Findet die stündliche Reihe in der Kachelmann-Antwort (tolerant)."""
    for key in ("hourly", "hours", "data", "forecast", "timesteps"):
        v = data.get(key)
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
        if isinstance(v, dict):
            for k2 in ("hourly", "hours", "data", "timesteps"):
                v2 = v.get(k2)
                if isinstance(v2, list) and v2 and isinstance(v2[0], dict):
                    return v2
    return []


def _parse_forecast(data: dict, horizons: tuple[int, ...]) -> ForecastResult | None:
    rows = _extract_hourly(data)
    if not rows:
        return None

    # Optional: Zeitstempel für saubere Indexierung; sonst Listenindex = Stunde ab jetzt
    times = _parse_timestamps([
        str(_pick(r, "time", "timestamp", "validTime", "date") or "") for r in rows
    ])

    def _row_at(h: int) -> dict | None:
        if h < len(rows):
            return rows[h]
        return None

    horizons_out: list[ForecastHorizon] = []
    for h in horizons:
        # akkumulierter Niederschlag bis +h (Summe der stündlichen Werte)
        acc = 0.0
        have_prec = False
        for i in range(min(h + 1, len(rows))):
            p = _safe_float(_pick(rows[i], "precipitation", "prec", "rr", "rain"))
            if p is not None:
                acc += p
                have_prec = True

        row = _row_at(h)
        temp = wind = gust = None
        if row is not None:
            temp = _safe_float(_pick(row, "temperature", "temp", "t2m"))
            wind = _norm_wind_ms(_safe_float(_pick(row, "windSpeed", "wind", "ff")))
            gust = _norm_wind_ms(_safe_float(_pick(row, "windGust", "gust", "fx")))

        horizons_out.append(ForecastHorizon(
            hours=h,
            precipitation_acc_mm=acc if have_prec else None,
            temperature_c=temp,
            wind_speed_ms=wind,
            gust_speed_ms=gust,
        ))

    # Wenn gar keine verwertbaren Werte → None (Fallback)
    if all(
        h.precipitation_acc_mm is None and h.temperature_c is None and h.wind_speed_ms is None
        for h in horizons_out
    ):
        return None

    _ = times  # reserviert für künftige zeitstempel-genaue Indexierung
    return ForecastResult(horizons=horizons_out, source=_SOURCE)
