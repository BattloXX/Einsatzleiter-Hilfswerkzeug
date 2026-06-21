"""Geräteverleih – Geschäftslogik."""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models.major_incident import IncidentSite
from app.models.master import OrgSettings
from app.models.verleih import (
    VerleihArtikel,
    VerleihAusleihe,
    VerleihPosition,
    VerleihStatus,
    VerleihStueckliste,
)


def get_org_settings(db: Session, org_id: int) -> OrgSettings | None:
    return db.query(OrgSettings).filter_by(org_id=org_id).first()


def get_artikel_aktiv(db: Session) -> list[VerleihArtikel]:
    return db.query(VerleihArtikel).filter_by(aktiv=True).order_by(VerleihArtikel.bezeichnung).all()


def get_stuecklisten_aktiv(db: Session) -> list[VerleihStueckliste]:
    return (
        db.query(VerleihStueckliste)
        .filter_by(aktiv=True)
        .options(selectinload(VerleihStueckliste.positionen))
        .order_by(VerleihStueckliste.bezeichnung)
        .all()
    )


def get_ausleihen_fuer_lage(db: Session, lage_id: int) -> list[VerleihAusleihe]:
    return (
        db.query(VerleihAusleihe)
        .filter_by(lage_id=lage_id)
        .options(
            selectinload(VerleihAusleihe.positionen),
        )
        .order_by(VerleihAusleihe.ausgeliehen_at.desc())
        .all()
    )


def create_ausleihe(
    db: Session,
    lage_id: int,
    org_id: int,
    name: str,
    adresse: str | None,
    telefon: str | None,
    site_id: int | None,
    positionen: list[dict],
    user_id: int | None,
) -> VerleihAusleihe:
    org = get_org_settings(db, org_id)
    erinnerung_stunden = org.gsl_verleih_erinnerung_stunden if org else None

    ausleihe = VerleihAusleihe(
        org_id=org_id,
        lage_id=lage_id,
        site_id=site_id,
        name=name,
        adresse=adresse or None,
        telefon=telefon or None,
        created_by_user_id=user_id,
    )
    if erinnerung_stunden:
        ausleihe.erinnerung_geplant_at = datetime.now(UTC) + timedelta(hours=erinnerung_stunden)

    db.add(ausleihe)
    db.flush()

    for p in positionen:
        pos = VerleihPosition(
            ausleihe_id=ausleihe.id,
            org_id=org_id,
            artikel_id=p.get("artikel_id"),
            bezeichnung=p["bezeichnung"],
            artikel_nr=p.get("artikel_nr"),
            menge=int(p.get("menge", 1)),
        )
        db.add(pos)

    db.commit()
    db.refresh(ausleihe)
    return ausleihe


def return_position(db: Session, position_id: int) -> VerleihAusleihe:
    pos = db.get(VerleihPosition, position_id)
    if not pos:
        raise ValueError("Position nicht gefunden")
    pos.status = VerleihStatus.zurueckgegeben
    pos.zurueckgegeben_at = datetime.now(UTC)

    ausleihe = db.get(VerleihAusleihe, pos.ausleihe_id)
    _update_ausleihe_status(db, ausleihe)
    db.commit()
    return ausleihe


def return_all(db: Session, ausleihe_id: int) -> VerleihAusleihe:
    ausleihe = db.get(VerleihAusleihe, ausleihe_id)
    if not ausleihe:
        raise ValueError("Ausleihe nicht gefunden")
    now = datetime.now(UTC)
    for pos in ausleihe.positionen:
        if pos.status == VerleihStatus.ausgeliehen:
            pos.status = VerleihStatus.zurueckgegeben
            pos.zurueckgegeben_at = now
    _update_ausleihe_status(db, ausleihe)
    db.commit()
    return ausleihe


def _update_ausleihe_status(db: Session, ausleihe: VerleihAusleihe) -> None:
    # Force refresh positionen
    db.refresh(ausleihe)
    alle_zurueck = all(p.status == VerleihStatus.zurueckgegeben for p in ausleihe.positionen)
    if alle_zurueck and ausleihe.status != VerleihStatus.zurueckgegeben:
        ausleihe.status = VerleihStatus.zurueckgegeben
        ausleihe.zurueckgegeben_at = datetime.now(UTC)


def generate_pin() -> str:
    return str(secrets.randbelow(1_000_000)).zfill(6)


def get_sms_ausleih_text(db: Session, org_id: int, ausleihe: VerleihAusleihe) -> str:
    org = get_org_settings(db, org_id)
    artikel = ausleihe.artikel_bezeichnungen or "Material"
    org_name = "Feuerwehr"
    try:
        from app.models.master import FireDept
        dept = db.get(FireDept, org_id)
        if dept:
            org_name = dept.name
    except Exception:
        pass
    template = (org.gsl_verleih_sms_ausleih_text if org else None) or (
        "Das Material ({artikel}) wurde an Sie ausgeliehen. "
        "Bitte bringen Sie es schnellstmoeglich zurueck. - {org}"
    )
    return template.replace("{artikel}", artikel).replace("{org}", org_name).replace("{name}", ausleihe.name)


def get_sms_erinnerung_text(db: Session, org_id: int, ausleihe: VerleihAusleihe) -> str:
    org = get_org_settings(db, org_id)
    artikel = ausleihe.artikel_bezeichnungen or "Material"
    org_name = "Feuerwehr"
    try:
        from app.models.master import FireDept
        dept = db.get(FireDept, org_id)
        if dept:
            org_name = dept.name
    except Exception:
        pass
    template = (org.gsl_verleih_sms_erinnerung_text if org else None) or (
        "Erinnerung: Bitte bringen Sie das ausgeliehene Material ({artikel}) "
        "umgehend zurueck. - {org}"
    )
    return template.replace("{artikel}", artikel).replace("{org}", org_name).replace("{name}", ausleihe.name)
