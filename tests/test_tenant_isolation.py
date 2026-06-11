"""Tenant-Isolation-Tests (PR 1 Grundlage).

Akzeptanz-Kriterium: ungefiltertes select(Member) liefert nur Org-A-Daten,
wenn Org A im Session-Kontext gesetzt ist – obwohl beide Orgs in der DB liegen.

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
from app.models.master import FireDept, Member
from app.models.user import Role


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
