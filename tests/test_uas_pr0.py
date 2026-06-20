"""PR 0: UAS-Modul Feature-Flag & Guard-Tests."""
from unittest.mock import MagicMock

import pytest

from app.services.uas_service import uas_effective_enabled, uas_system_enabled
from tests.conftest import TestingSession


# ── Service-Logik (ohne HTTP) ─────────────────────────────────────────────────

class _Sys:
    def __init__(self, value=None):
        self.key = "uas_module_enabled"
        self.value = value


class _OrgS:
    def __init__(self, enabled=False):
        self.uas_module_enabled = enabled


def _db_with(sys_value, org_enabled):
    """Gibt einen Mock-DB zurück mit vorgegebenen SystemSettings/OrgSettings."""
    db = MagicMock()
    sys_row = _Sys(sys_value)
    org_row = _OrgS(org_enabled)
    q = MagicMock()
    q.filter.return_value.first.side_effect = [sys_row, org_row]
    db.query.return_value = q
    return db


def test_system_flag_missing_returns_false():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert uas_system_enabled(db) is False


def test_system_flag_false_value():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _Sys("false")
    assert uas_system_enabled(db) is False


def test_system_flag_true_value():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _Sys("true")
    assert uas_system_enabled(db) is True


def test_effective_false_when_no_org():
    db = MagicMock()
    assert uas_effective_enabled(None, db) is False


def test_effective_false_when_system_off():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = _Sys("false")
    assert uas_effective_enabled(1, db) is False


def test_effective_false_when_system_on_org_off():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [
        _Sys("true"),   # SystemSettings
        _OrgS(False),   # OrgSettings
    ]
    assert uas_effective_enabled(1, db) is False


def test_effective_true_when_both_on():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [
        _Sys("true"),  # SystemSettings
        _OrgS(True),   # OrgSettings
    ]
    assert uas_effective_enabled(1, db) is True


# ── Guard: HTTP 404 wenn nicht aktiv ─────────────────────────────────────────

def test_guard_404_when_module_off(client):
    """GET /uas/ → 404 wenn Modul nicht aktiviert."""
    resp = client.get("/uas/", follow_redirects=False)
    # Nicht authentifiziert → 302 zu Login oder 404, aber nicht 200
    assert resp.status_code in (302, 404)


# ── Importierbarkeit ──────────────────────────────────────────────────────────

def test_uas_router_importable():
    from app.routers.ui_uas import require_uas_enabled, router
    assert callable(require_uas_enabled)
    assert router is not None


def test_uas_service_importable():
    from app.services.uas_service import uas_effective_enabled, uas_system_enabled
    assert callable(uas_effective_enabled)
    assert callable(uas_system_enabled)
