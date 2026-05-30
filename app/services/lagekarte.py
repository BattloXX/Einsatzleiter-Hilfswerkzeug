"""Lagekarte.info Hilfsfunktionen: URL-Erzeugung, GeoJSON-Feature-Bau, Koordinaten-Jitter."""
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.incident import Incident

# Wolfurt als letzter Fallback (wird nur verwendet, wenn weder Einsatz- noch Org-Koordinaten gesetzt)
FALLBACK_LAT = 47.4664
FALLBACK_LNG = 9.7416

# Deterministischer Streuradius für Fahrzeuge ohne eigene Position (~15 m)
_JITTER_RADIUS_DEG = 0.000135


def build_einsatz_url(lat: float, lng: float) -> str:
    return f"https://www.lagekarte.info/?einsatz={lat},{lng}"


def resolve_lagekarte_url(incident: "Incident") -> str | None:
    """Gibt die URL zurück, die im Lagekarte.info-Button verwendet wird.

    Priorität: gespeicherter SHASH/beliebiger Link > generierter Einsatz-Link > None.
    """
    if incident.lagekarte_shash_url:
        return incident.lagekarte_shash_url
    if incident.lat is not None and incident.lng is not None:
        return build_einsatz_url(incident.lat, incident.lng)
    return None


def scatter_coords(base_lat: float, base_lng: float, index: int, count: int) -> tuple[float, float]:
    """Deterministisches Kreisstreuung für Fahrzeuge ohne eigene Position.

    Alle Fahrzeuge werden gleichmäßig auf einem kleinen Kreis um den
    Einsatz-Mittelpunkt verteilt. Bei count=1 liegt der Punkt direkt auf dem
    Mittelpunkt (kein Jitter nötig). Index ist 0-basiert.
    """
    if count <= 1:
        return base_lat, base_lng
    angle = (2 * math.pi * index) / count
    lat = base_lat + _JITTER_RADIUS_DEG * math.cos(angle)
    lng = base_lng + _JITTER_RADIUS_DEG * math.sin(angle) / math.cos(math.radians(base_lat))
    return lat, lng


def _live_position(db: "Session", vehicle_master_id: int) -> tuple[float, float] | None:
    """Gibt die zuletzt gemeldete GPS-Position eines Fahrzeugs zurück, wenn frisch genug.

    Frisch = in den letzten 5 Minuten übermittelt. Ältere Positionen werden ignoriert,
    damit das Fahrzeug beim Einsatzende nicht dauerhaft an der letzten Koordinate hängt.
    """
    from datetime import UTC, datetime, timedelta
    from app.models.user import DeviceToken
    threshold = datetime.now(UTC) - timedelta(minutes=5)
    dt = (
        db.query(DeviceToken)
        .filter(
            DeviceToken.vehicle_master_id == vehicle_master_id,
            DeviceToken.revoked_at.is_(None),
            DeviceToken.last_lat.isnot(None),
            DeviceToken.last_lng.isnot(None),
            DeviceToken.last_location_at >= threshold,
        )
        .order_by(DeviceToken.last_location_at.desc())
        .first()
    )
    if dt and dt.last_lat is not None and dt.last_lng is not None:
        return dt.last_lat, dt.last_lng
    return None


def vehicle_features(db: "Session", incident: "Incident") -> list[dict]:
    """Baut GeoJSON-Features für alle aktiven Fahrzeuge eines Einsatzes.

    Koordinaten: echte GPS-Position falls vorhanden (live übermittelt vom Gerät),
    sonst deterministischer Jitter um den Einsatz-Mittelpunkt.
    Wenn keine Einsatz-Koordinaten → leere Liste.
    """
    if incident.lat is None or incident.lng is None:
        return []

    active_vehicles = [v for v in incident.vehicles if v.removed_at is None]
    count = len(active_vehicles)
    features = []

    for idx, iv in enumerate(active_vehicles):
        vm = iv.vehicle_master
        # Echte Position bevorzugen, falls frisch vorhanden
        live = _live_position(db, vm.id) if vm else None
        if live:
            lat, lng = live
        else:
            lat, lng = scatter_coords(incident.lat, incident.lng, idx, count)

        open_tasks = iv.open_task_count
        info = f"{open_tasks} offene Aufgabe{'n' if open_tasks != 1 else ''}" if open_tasks else ""

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat],  # GeoJSON: [lng, lat]
            },
            "properties": {
                "name": vm.display_label if vm else "",
                "typ": (vm.type or vm.name) if vm else "",
                "status": iv.unit_status,
                "info": info,
                "einsatz_id": incident.id,
                "fahrzeug_id": iv.id,
                "live_position": live is not None,
            },
        }
        features.append(feature)

    return features
