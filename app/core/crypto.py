"""Fernet-Verschlüsselungs-Helfer (gemeinsam für SSO-Secret und KI-API-Key)."""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(raw: str) -> str:
    return _fernet().encrypt(raw.encode()).decode()


def decrypt_secret(enc: str) -> str:
    return _fernet().decrypt(enc.encode()).decode()
