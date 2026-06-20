"""PR 8: Medien & DSGVO-Workflow (Model, Enums, Tenant, DB-Roundtrip)."""
from datetime import date

import pytest

from app.models.uas import UASMedien, UASMedienDsgvoStatus, UASMedienTyp


def test_uas_medien_importable():
    assert UASMedien.__tablename__ == "uas_medien"


def test_medientyp_werte():
    values = {t.value for t in UASMedienTyp}
    assert "foto" in values
    assert "video" in values
    assert "dokument" in values
    assert "sonstiges" in values
    assert len(values) == 4


def test_dsgvo_status_werte():
    values = {s.value for s in UASMedienDsgvoStatus}
    assert "erfasst" in values
    assert "begruendet" in values
    assert "zur_loeschung" in values
    assert "geloescht" in values
    assert len(values) == 4


def test_tenant_tables_medien():
    from app.core.tenant import _TENANT_TABLE_NAMES
    assert "uas_medien" in _TENANT_TABLE_NAMES


@pytest.fixture
def db_ctx():
    from app.core.tenant import set_tenant_context
    from tests.conftest import TestingSession
    db = TestingSession()
    set_tenant_context(db, None)
    yield db
    db.close()


def test_medien_db_create(setup_db, db_ctx):
    m = UASMedien(
        org_id=1,
        uas_flug_id=None,
        uas_einsatz_id=None,
        dateiname="drohne_foto_001.jpg",
        dateipfad="",
        medientyp=UASMedienTyp.foto.value,
        dsgvo_status=UASMedienDsgvoStatus.begruendet.value,
        begruendung="Einsatzrelevante Aufnahme Absturzstelle",
        loeschfrist=date(2026, 7, 20),
    )
    db_ctx.add(m)
    db_ctx.commit()
    db_ctx.refresh(m)

    assert m.id is not None
    assert m.dateiname == "drohne_foto_001.jpg"
    assert m.dsgvo_status == "begruendet"
    assert m.loeschfrist == date(2026, 7, 20)


def test_medien_default_status(setup_db, db_ctx):
    m = UASMedien(
        org_id=1,
        dateiname="video_002.mp4",
        dateipfad="",
    )
    db_ctx.add(m)
    db_ctx.commit()
    db_ctx.refresh(m)
    assert m.dsgvo_status == "erfasst"
    assert m.medientyp == "foto"  # default


def test_medien_loeschfrist_leer(setup_db, db_ctx):
    m = UASMedien(org_id=1, dateiname="test.jpg", dateipfad="")
    db_ctx.add(m)
    db_ctx.commit()
    db_ctx.refresh(m)
    assert m.loeschfrist is None
    assert m.geloescht_at is None
