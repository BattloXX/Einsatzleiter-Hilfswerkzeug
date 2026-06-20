"""PR 1: UAS-Stammdaten Modelle & Migration roundtrip (SQLite)."""
import secrets
from datetime import date

import pytest

from app.core.tenant import set_tenant_context
from app.models.uas import (
    UASBosStufe,
    UASDevice,
    UASDeviceCeKlasse,
    UASDeviceStatus,
    UASDeviceUnterkategorie,
    UASFlugbewegung,
    UASFlugbewegungArt,
    UASPilot,
    UASWartung,
    UASWartungArt,
    UASWartungErgebnis,
)
from tests.conftest import TestingSession


# ── Importierbarkeit ──────────────────────────────────────────────────────────

def test_uas_models_importable():
    from app.models.uas import UASDevice, UASPilot, UASFlugbewegung, UASWartung
    assert UASDevice.__tablename__ == "uas_device"
    assert UASPilot.__tablename__ == "uas_pilot"
    assert UASFlugbewegung.__tablename__ == "uas_flugbewegung"
    assert UASWartung.__tablename__ == "uas_wartung"


def test_enums_defined():
    assert UASDeviceCeKlasse.C2 == "C2"
    assert UASDeviceUnterkategorie.A2 == "A2"
    assert UASDeviceStatus.aktiv == "aktiv"
    assert UASBosStufe.stufe_1 == "1"
    assert UASWartungArt.monatliche_sichtkontrolle == "monatliche_sichtkontrolle"
    assert UASWartungErgebnis.io == "io"
    assert UASFlugbewegungArt.einsatz == "einsatz"


# ── DB-Roundtrip (SQLite) ─────────────────────────────────────────────────────

@pytest.fixture
def db_ctx():
    db = TestingSession()
    set_tenant_context(db, None)
    yield db
    db.rollback()
    db.close()


def test_device_create_and_read(db_ctx):
    db = db_ctx
    dev = UASDevice(
        org_id=1,
        bezeichnung="DJI Mavic 3E Test",
        hersteller="DJI",
        typ="Mavic 3E",
        registriernummer="AT-12345-TEST",
        ce_klasse=UASDeviceCeKlasse.C2.value,
        unterkategorie=UASDeviceUnterkategorie.A2.value,
        mtom_g=920,
        versicherung_polizze="POL-001",
        versicherung_gueltig_bis=date(2027, 12, 31),
        status=UASDeviceStatus.aktiv.value,
    )
    db.add(dev)
    db.flush()
    assert dev.id is not None
    assert dev.qr_token  # auto-generiert
    assert dev.status == "aktiv"


def test_pilot_create_and_read(db_ctx):
    db = db_ctx
    pilot = UASPilot(
        org_id=1,
        nachname="Muster",
        vorname="Max",
        geburtsdatum=date(1990, 1, 1),
        ist_truppfuehrer=True,
        a1a3_id="A1A3-TEST-001",
        a1a3_gueltig_bis=date(2027, 6, 1),
        a2_id="A2-TEST-001",
        a2_gueltig_bis=date(2027, 6, 1),
        bos_stufe=UASBosStufe.stufe_1.value,
        lfv_zugelassen=True,
        aktiv=True,
    )
    db.add(pilot)
    db.flush()
    assert pilot.id is not None
    assert pilot.bos_stufe == "1"


def test_wartung_linked_to_device(db_ctx):
    db = db_ctx
    dev = UASDevice(
        org_id=1,
        bezeichnung="Wartungstest-Gerät",
        qr_token=secrets.token_urlsafe(32),
    )
    db.add(dev)
    db.flush()

    wartung = UASWartung(
        org_id=1,
        device_id=dev.id,
        datum=date(2026, 6, 1),
        art=UASWartungArt.monatliche_sichtkontrolle.value,
        ergebnis=UASWartungErgebnis.io.value,
        pruefer="Max Muster",
    )
    db.add(wartung)
    db.flush()
    assert wartung.id is not None


def test_flugbewegung_linked_to_pilot(db_ctx):
    db = db_ctx
    pilot = UASPilot(org_id=1, nachname="Test", vorname="Pilot", aktiv=True)
    db.add(pilot)
    db.flush()

    bewegung = UASFlugbewegung(
        org_id=1,
        pilot_id=pilot.id,
        datum=date(2026, 6, 1),
        dauer_min=15,
        art=UASFlugbewegungArt.einsatz.value,
    )
    db.add(bewegung)
    db.flush()
    assert bewegung.id is not None


def test_tenant_tables_registered():
    from app.core.tenant import _TENANT_TABLE_NAMES
    assert "uas_device" in _TENANT_TABLE_NAMES
    assert "uas_pilot" in _TENANT_TABLE_NAMES
    assert "uas_flugbewegung" in _TENANT_TABLE_NAMES
    assert "uas_wartung" in _TENANT_TABLE_NAMES
