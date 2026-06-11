"""Tenant-Isolation-Tests (PR 1 + PR 2 Grundlage).

Akzeptanz-Kriterium PR 1: ungefiltertes select(Member) liefert nur Org-A-Daten,
wenn Org A im Session-Kontext gesetzt ist – obwohl beide Orgs in der DB liegen.

Akzeptanz-Kriterium PR 2: Zwei Orgs können beide Alarmtyp 'B3' mit unterschiedlichem
Label führen; get_alarm_type_by_code liefert org-scoped Ergebnis.

Diese Fixture wird in jedem Folge-PR um neue Endpoints erweitert.
"""
import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

# BigInteger → INTEGER für SQLite-Testumgebung
@compiles(BigInteger, "sqlite")
def _bigint_sqlite(element, compiler, **kw):
    return "INTEGER"


from app.core.tenant import set_tenant_context
from app.db import Base
from app.models.master import AlarmType, FireDept, Member
from app.models.user import Role
from app.services.alarm_service import get_alarm_type_by_code


TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def isolation_db():
    """Eigene In-Memory-DB für Isolation-Tests (unabhängig von conftest.py)."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Zwei unabhängige Orgs
    org_a = FireDept(slug="org-a", name="Org A", color="#ff0000", bos="Feuerwehr")
    org_b = FireDept(slug="org-b", name="Org B", color="#0000ff", bos="Feuerwehr")
    db.add_all([org_a, org_b])
    db.flush()

    # Je 2 Members pro Org
    db.add_all([
        Member(org_id=org_a.id, firstname="Anna", lastname="Alpha"),
        Member(org_id=org_a.id, firstname="Anton", lastname="Alpha"),
        Member(org_id=org_b.id, firstname="Bernd", lastname="Beta"),
        Member(org_id=org_b.id, firstname="Berta", lastname="Beta"),
    ])
    db.commit()

    yield db, org_a.id, org_b.id

    db.close()
    Base.metadata.drop_all(bind=engine)


def test_tenant_filter_org_a(isolation_db):
    """Mit Org-A-Kontext: nur Org-A-Members sichtbar."""
    db, org_a_id, org_b_id = isolation_db
    set_tenant_context(db, org_a_id)

    members = db.query(Member).all()

    assert len(members) == 2
    assert all(m.org_id == org_a_id for m in members)
    lastnames = {m.lastname for m in members}
    assert lastnames == {"Alpha"}


def test_tenant_filter_org_b(isolation_db):
    """Mit Org-B-Kontext: nur Org-B-Members sichtbar."""
    db, org_a_id, org_b_id = isolation_db
    set_tenant_context(db, org_b_id)

    members = db.query(Member).all()

    assert len(members) == 2
    assert all(m.org_id == org_b_id for m in members)
    lastnames = {m.lastname for m in members}
    assert lastnames == {"Beta"}


def test_tenant_filter_none_sees_all(isolation_db):
    """Ohne Tenant-Kontext (system_admin): alle Members sichtbar."""
    db, org_a_id, org_b_id = isolation_db
    set_tenant_context(db, None)

    members = db.query(Member).all()

    assert len(members) == 4


def test_tenant_filter_include_all_tenants_bypass(isolation_db):
    """execution_option include_all_tenants=True umgeht den Filter."""
    db, org_a_id, org_b_id = isolation_db
    set_tenant_context(db, org_a_id)

    from sqlalchemy import select
    members = db.execute(
        select(Member).execution_options(include_all_tenants=True)
    ).scalars().unique().all()

    assert len(members) == 4


def test_no_cross_tenant_leak(isolation_db):
    """Org A kann keinen Member von Org B über .get() finden wenn Filter aktiv."""
    db, org_a_id, org_b_id = isolation_db
    set_tenant_context(db, None)

    # Hole eine Org-B-Member-ID
    b_member = db.query(Member).filter(Member.org_id == org_b_id).first()
    assert b_member is not None
    b_member_id = b_member.id

    # Jetzt Org-A-Kontext setzen und versuchen Org-B-Member abzufragen
    set_tenant_context(db, org_a_id)
    db.expire_all()

    found = db.query(Member).filter(Member.id == b_member_id).first()
    assert found is None, "Org-A darf keinen Org-B-Member sehen!"


# ---------------------------------------------------------------------------
# PR 2: AlarmType-Isolation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def alarm_type_db():
    """Eigene In-Memory-DB für AlarmType-Isolationstests."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    org_a = FireDept(slug="at-org-a", name="AT Org A", color="#ff0000", bos="Feuerwehr")
    org_b = FireDept(slug="at-org-b", name="AT Org B", color="#0000ff", bos="Feuerwehr")
    db.add_all([org_a, org_b])
    db.flush()

    # Beide Orgs haben Alarmtyp 'B3' – mit unterschiedlichem Label (Akzeptanz-Kriterium PR 2)
    db.add_all([
        AlarmType(org_id=org_a.id, code="B3", category="B", label="Brand Mittel – Org A"),
        AlarmType(org_id=org_a.id, code="T1", category="T", label="Technisch Klein – Org A"),
        AlarmType(org_id=org_b.id, code="B3", category="B", label="Brand Mittel – Org B"),
        AlarmType(org_id=org_b.id, code="T2", category="T", label="Technisch Groß – Org B"),
    ])
    db.commit()

    yield db, org_a.id, org_b.id

    db.close()
    Base.metadata.drop_all(bind=engine)


def test_alarm_type_isolation_org_a(alarm_type_db):
    """Mit Org-A-Kontext: nur Org-A-AlarmTypes sichtbar."""
    db, org_a_id, org_b_id = alarm_type_db
    set_tenant_context(db, org_a_id)

    alarm_types = db.query(AlarmType).all()

    assert len(alarm_types) == 2
    assert all(at.org_id == org_a_id for at in alarm_types)
    codes = {at.code for at in alarm_types}
    assert codes == {"B3", "T1"}


def test_alarm_type_isolation_org_b(alarm_type_db):
    """Mit Org-B-Kontext: nur Org-B-AlarmTypes sichtbar."""
    db, org_a_id, org_b_id = alarm_type_db
    set_tenant_context(db, org_b_id)

    alarm_types = db.query(AlarmType).all()

    assert len(alarm_types) == 2
    assert all(at.org_id == org_b_id for at in alarm_types)
    codes = {at.code for at in alarm_types}
    assert codes == {"B3", "T2"}


def test_alarm_type_same_code_different_orgs(alarm_type_db):
    """Akzeptanz PR 2: Zwei Orgs können beide Code 'B3' mit unterschiedlichem Label führen."""
    db, org_a_id, org_b_id = alarm_type_db
    set_tenant_context(db, None)

    all_b3 = db.query(AlarmType).filter(AlarmType.code == "B3").all()

    assert len(all_b3) == 2
    labels = {at.label for at in all_b3}
    assert "Brand Mittel – Org A" in labels
    assert "Brand Mittel – Org B" in labels
    org_ids = {at.org_id for at in all_b3}
    assert org_ids == {org_a_id, org_b_id}


def test_get_alarm_type_by_code_org_scoped(alarm_type_db):
    """get_alarm_type_by_code gibt den Alarmtyp der richtigen Org zurück."""
    db, org_a_id, org_b_id = alarm_type_db
    set_tenant_context(db, None)

    at_a = get_alarm_type_by_code(db, org_a_id, "B3")
    at_b = get_alarm_type_by_code(db, org_b_id, "B3")

    assert at_a is not None
    assert at_b is not None
    assert at_a.id != at_b.id
    assert at_a.label == "Brand Mittel – Org A"
    assert at_b.label == "Brand Mittel – Org B"


def test_get_alarm_type_by_code_missing_returns_none(alarm_type_db):
    """get_alarm_type_by_code liefert None für nicht existierenden Code."""
    db, org_a_id, _ = alarm_type_db
    set_tenant_context(db, None)

    result = get_alarm_type_by_code(db, org_a_id, "NONEXISTENT")

    assert result is None


def test_alarm_type_no_cross_tenant_leak(alarm_type_db):
    """Org A kann Alarmtyp 'T2' (nur Org B) nicht sehen wenn Filter aktiv."""
    db, org_a_id, org_b_id = alarm_type_db
    set_tenant_context(db, org_a_id)
    db.expire_all()

    result = db.query(AlarmType).filter(AlarmType.code == "T2").first()

    assert result is None, "Org-A darf keinen Org-B-AlarmType sehen!"
