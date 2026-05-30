"""Gerät-API: FCM-Token-Registrierung, Standort-Tracking, Dienst-Status.

Diese Endpoints werden von der nativen Android-App (Capacitor) aufgerufen.
Auth über bestehende Session-Cookies (Device-Login via /geraet-login).
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import DeviceToken, FcmToken

router = APIRouter(prefix="/api/v1/device", tags=["device"])


def _get_device_token(user_id: int, db: Session) -> DeviceToken | None:
    """Gibt das aktive DeviceToken des Users zurück (neuestes nicht-widerrufenes)."""
    return (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == user_id, DeviceToken.revoked_at.is_(None))
        .order_by(DeviceToken.created_at.desc())
        .first()
    )


# ── FCM-Token ─────────────────────────────────────────────────────────────────

@router.post("/fcm-token")
async def register_fcm_token(request: Request, db: Session = Depends(get_db)):
    """Registriert oder aktualisiert den FCM Registration Token des eingeloggten Geräts."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    data = await request.json()
    token = (data.get("token") or "").strip()
    platform = (data.get("platform") or "android").strip()[:20]
    if not token:
        raise HTTPException(status_code=400, detail="token fehlt")

    now = datetime.now(UTC)
    device_token = _get_device_token(user.id, db)

    # Upsert: vorhandenen Token updaten oder neuen anlegen
    existing = db.query(FcmToken).filter(FcmToken.token == token).first()
    if existing:
        existing.user_id = user.id
        existing.device_token_id = device_token.id if device_token else None
        existing.last_used_at = now
    else:
        db.add(FcmToken(
            user_id=user.id,
            device_token_id=device_token.id if device_token else None,
            token=token,
            platform=platform,
            created_at=now,
            last_used_at=now,
        ))
    db.commit()
    return JSONResponse({"ok": True})


@router.delete("/fcm-token")
async def unregister_fcm_token(request: Request, db: Session = Depends(get_db)):
    """Entfernt den FCM Token bei Logout oder Token-Rotation."""
    data = await request.json()
    token = (data.get("token") or "").strip()
    if token:
        db.query(FcmToken).filter(FcmToken.token == token).delete()
        db.commit()
    return JSONResponse({"ok": True})


# ── Standort ──────────────────────────────────────────────────────────────────

@router.post("/location")
async def update_location(request: Request, db: Session = Depends(get_db)):
    """Aktualisiert den Gerätestandort.

    Wird von der App nur bei aktivem Einsatz/Dienst aufgerufen (alle 10–30 s).
    Die Position erscheint auf der Lagekarte anstatt des Scatter-Punkts.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    data = await request.json()
    try:
        lat = float(data["lat"])
        lng = float(data["lng"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="lat/lng fehlen oder ungültig")

    device_token = _get_device_token(user.id, db)
    if not device_token:
        raise HTTPException(status_code=404, detail="Kein registriertes Gerät")

    device_token.last_lat = lat
    device_token.last_lng = lng
    device_token.last_location_at = datetime.now(UTC)
    db.commit()
    return JSONResponse({"ok": True})


# ── Dienst-Status ─────────────────────────────────────────────────────────────

@router.post("/duty")
async def set_duty(request: Request, db: Session = Depends(get_db)):
    """Setzt den Dienst-Status des Geräts (aktiv/inaktiv).

    Die App startet / stoppt das Background-Tracking entsprechend.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")
    data = await request.json()
    active = bool(data.get("active", False))

    device_token = _get_device_token(user.id, db)
    if not device_token:
        raise HTTPException(status_code=404, detail="Kein registriertes Gerät")

    device_token.duty_active = active
    db.commit()
    return JSONResponse({"ok": True, "duty_active": active})


@router.get("/duty-state")
async def get_duty_state(request: Request, db: Session = Depends(get_db)):
    """Gibt zurück, ob für das Gerät aktuell ein aktiver Einsatz vorliegt.

    Die App nutzt diesen Endpoint, um Standort-Tracking automatisch zu steuern.
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht eingeloggt")

    device_token = _get_device_token(user.id, db)
    if not device_token:
        return JSONResponse({"duty_active": False, "incident_active": False})

    # Prüfen ob dem Fahrzeug ein aktiver Einsatz zugewiesen ist
    incident_active = False
    if device_token.vehicle_master_id:
        from app.models.incident import Incident, IncidentVehicle
        incident_active = db.query(Incident).join(
            IncidentVehicle, Incident.id == IncidentVehicle.incident_id
        ).filter(
            IncidentVehicle.vehicle_master_id == device_token.vehicle_master_id,
            IncidentVehicle.removed_at.is_(None),
            Incident.status == "active",
        ).first() is not None

    return JSONResponse({
        "duty_active": device_token.duty_active,
        "incident_active": incident_active,
        "should_track": device_token.duty_active or incident_active,
    })
