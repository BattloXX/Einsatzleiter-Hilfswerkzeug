"""Regressionstest PR8 (KONS-1): lage_media_service nutzt dieselbe Bild-Pipeline
wie media_service._process_image (kein eigener Pillow-Code mehr) und reserviert
weiterhin die Speicher-Quota."""
import io

import pytest
from fastapi import UploadFile

from app.core.tenant import set_tenant_context
from app.services import lage_media_service


def _fake_upload(filename: str, data: bytes, content_type: str = "image/png") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(data), headers={"content-type": content_type})


def _make_png_bytes(w=800, h=600) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color=(200, 30, 30)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture()
def db_session(setup_db):
    from tests.conftest import TestingSession
    db = TestingSession()
    set_tenant_context(db, None)
    yield db
    db.rollback()
    db.close()


@pytest.mark.asyncio
async def test_upload_site_media_uses_shared_pipeline_and_reserves_quota(tmp_path, monkeypatch, db_session):
    from app.models.master import FireDept

    org = FireDept(slug="lage-media-dedup", name="Dedup Org", color="#ff0000", bos="Feuerwehr")
    db_session.add(org)
    db_session.flush()

    monkeypatch.setattr(lage_media_service, "_LAGE_MEDIA_DIR", str(tmp_path / "lage_media"))

    upload = _fake_upload("foto.png", _make_png_bytes())
    media = await lage_media_service.upload_site_media(
        upload, site_id=1, org_id=org.id, user_id=None, author_name="Test", db=db_session,
    )

    assert media.stored_filename.endswith(".jpg")
    stored = lage_media_service.site_media_path(media)
    assert stored.exists(), "Datei wurde nicht ueber die gemeinsame _process_image-Pipeline geschrieben"
    assert media.bytes > 0

    from app.services.storage_service import get_org_storage_info
    info = get_org_storage_info(db_session, org.id)
    assert info["used_bytes"] == media.bytes, "Quota wurde nicht reserviert (KONS-1-Regression)"
