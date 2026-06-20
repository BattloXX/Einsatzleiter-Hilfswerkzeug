"""Fernet-Verschlüsselungs-Helfer (gemeinsam für SSO-Secret und KI-API-Key).

Schlüssel-Hierarchie (F-03):
  1. FERNET_KEY gesetzt → direkt verwenden (empfohlen, unabhängig rotierbar).
  2. Fallback: SHA256("fernet-v1:" + SECRET_KEY) — abwärtskompatibel, aber
     an SECRET_KEY-Rotation gekoppelt.
"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _fernet() -> Fernet:
    if settings.FERNET_KEY:
        return Fernet(settings.FERNET_KEY.encode())
    # Fallback: domain-getrennter Ableitungsstring (verhindert Key-Reuse mit Sessions)
    raw = f"fernet-v1:{settings.SECRET_KEY}".encode()
    key = hashlib.sha256(raw).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(raw: str) -> str:
    return _fernet().encrypt(raw.encode()).decode()


def decrypt_secret(enc: str) -> str:
    return _fernet().decrypt(enc.encode()).decode()
