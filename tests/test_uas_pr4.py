"""PR 4: Flugbuch-Berechnungen, Checklisten, Audit-Hash, DB-Roundtrip."""
from datetime import datetime, UTC, timedelta

import pytest

from app.services.uas_flugbuch import (
    CHECKLISTE_NACHFLUG,
    CHECKLISTE_VORFLUG,
    berechne_dauer_min,
    berechne_flugsicherheitswerte,
    inhalt_hash,
    pruefe_1zu1_regel,
)


# ── Berechnungen (RL Anh. 8.2 v9) ────────────────────────────────────────────

def test_contingency_volume():
    result = berechne_flugsicherheitswerte(100.0)
    assert result["contingency_volume_m"] == 10.0


def test_ground_risk_buffer():
    result = berechne_flugsicherheitswerte(100.0)
    assert result["ground_risk_buffer_m"] == 110.0


def test_abstand_menschenansammlung():
    result = berechne_flugsicherheitswerte(100.0)
    # GRB(110) + CV(10) + 120 = 240
    assert result["abstand_menschenansammlung_m"] == 240.0


def test_sicherheitswerte_klein():
    r = berechne_flugsicherheitswerte(30.0)
    assert r["contingency_volume_m"] == 3.0
    assert r["ground_risk_buffer_m"] == 33.0


# ── 1:1-Regel ─────────────────────────────────────────────────────────────────

def test_1zu1_konform():
    assert pruefe_1zu1_regel(50.0, 55.0) is True


def test_1zu1_nicht_konform():
    assert pruefe_1zu1_regel(50.0, 40.0) is False


def test_1zu1_kein_abstand():
    assert pruefe_1zu1_regel(50.0, None) is False


# ── Dauarberechnung ───────────────────────────────────────────────────────────

def test_dauer_berechnung():
    start = datetime(2026, 6, 20, 10, 0, tzinfo=UTC)
    land = datetime(2026, 6, 20, 10, 25, tzinfo=UTC)
    assert berechne_dauer_min(start, land) == 25


def test_dauer_none_wenn_kein_start():
    assert berechne_dauer_min(None, datetime.now(UTC)) is None


def test_dauer_none_wenn_keine_landung():
    assert berechne_dauer_min(datetime.now(UTC), None) is None


# ── Checklisten-Seeds ─────────────────────────────────────────────────────────

def test_vorflug_checkliste_hat_pflichtpunkte():
    keys = {p["key"] for p in CHECKLISTE_VORFLUG}
    assert "v01" in keys  # Grundlage
    assert "v08" in keys  # 1:1-Regel
    assert len(CHECKLISTE_VORFLUG) >= 15


def test_nachflug_checkliste_not_empty():
    assert len(CHECKLISTE_NACHFLUG) >= 5
    assert all("key" in p and "label" in p for p in CHECKLISTE_NACHFLUG)


def test_vorflug_punkte_initial_false():
    assert all(p["erledigt"] is False for p in CHECKLISTE_VORFLUG)


# ── Audit-Hash ────────────────────────────────────────────────────────────────

def test_hash_deterministisch():
    data = {"id": 1, "datum": "2026-06-20", "dauer_min": 30}
    assert inhalt_hash(data) == inhalt_hash(data)


def test_hash_verschieden_bei_anderen_daten():
    d1 = {"id": 1, "dauer_min": 10}
    d2 = {"id": 1, "dauer_min": 20}
    assert inhalt_hash(d1) != inhalt_hash(d2)


def test_hash_laenge():
    assert len(inhalt_hash({"x": 1})) == 64


# ── Model-Import ──────────────────────────────────────────────────────────────

def test_uas_flug_importable():
    from app.models.uas import UASFlug, UASCheckliste
    assert UASFlug.__tablename__ == "uas_flug"
    assert UASCheckliste.__tablename__ == "uas_checkliste"


def test_flug_enums():
    from app.models.uas import UASFlugDurchfuehrung, UASFlugGrundlage, UASFlugStatus, UASChecklisteTyp
    assert "vlos" in {v.value for v in UASFlugDurchfuehrung}
    assert "bvlos" in {v.value for v in UASFlugDurchfuehrung}
    assert "open_a2" in {v.value for v in UASFlugGrundlage}
    assert "specific_bescheid" in {v.value for v in UASFlugGrundlage}
    assert "abgeschlossen" in {v.value for v in UASFlugStatus}
    assert "vorflug" in {v.value for v in UASChecklisteTyp}


def test_tenant_tables_flug():
    from app.core.tenant import _TENANT_TABLE_NAMES
    assert "uas_flug" in _TENANT_TABLE_NAMES
    assert "uas_checkliste" in _TENANT_TABLE_NAMES


# ── DB-Roundtrip ──────────────────────────────────────────────────────────────

@pytest.fixture
def db_ctx():
    from app.core.tenant import set_tenant_context
    from tests.conftest import TestingSession
    db = TestingSession()
    set_tenant_context(db, None)
    yield db
    db.close()


def test_uas_flug_db_create(setup_db, db_ctx):
    from datetime import date
    from app.models.uas import UASEinsatz, UASFlug, UASEinsatzStatus, UASFlugStatus

    einsatz = UASEinsatz(org_id=1, incident_id=997, status=UASEinsatzStatus.alarmiert.value)
    db_ctx.add(einsatz)
    db_ctx.flush()

    flug = UASFlug(
        org_id=1,
        uas_einsatz_id=einsatz.id,
        lfd_nr=1,
        datum=date(2026, 6, 20),
        durchfuehrung="vlos",
        grundlage="open_a2",
        geplante_flughoehe_m=50.0,
        status=UASFlugStatus.offen.value,
    )
    db_ctx.add(flug)
    db_ctx.commit()
    db_ctx.refresh(flug)

    assert flug.id is not None
    assert flug.grundlage == "open_a2"
    assert flug.geplante_flughoehe_m == 50.0
