"""UAS-Modul-Service: Feature-Flag-Logik.

Effektive Aktivierung: System-Flag (SystemSettings key "uas_module_enabled" == "true")
UND Org-Flag (OrgSettings.uas_module_enabled == True).
"""
from __future__ import annotations

from sqlalchemy.orm import Session


def uas_system_enabled(db: Session) -> bool:
    """Systemweiter UAS-Flag aus SystemSettings. Fehlender Key → False."""
    from app.models.master import SystemSettings
    row = db.query(SystemSettings).filter(SystemSettings.key == "uas_module_enabled").first()
    return row is not None and row.value == "true"


def uas_effective_enabled(org_id: int | None, db: Session) -> bool:
    """UAS effektiv aktiv ⟺ System-Flag AN und Org-Flag AN.

    Gibt False wenn org_id None (system_admin ohne Impersonation).
    """
    if org_id is None:
        return False
    if not uas_system_enabled(db):
        return False
    from app.models.master import OrgSettings
    org_s = db.query(OrgSettings).filter(OrgSettings.org_id == org_id).first()
    return bool(org_s and org_s.uas_module_enabled)
