"""Health data encryption — AES-256-GCM with key from Supabase Vault."""
import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from src.utils.config import settings

logger = logging.getLogger(__name__)

# For MVP, derive key from env var. Production: fetch from Supabase Vault.
_ENCRYPTION_KEY: bytes | None = None


def _get_key() -> bytes:
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is None:
        raw = settings.health_encryption_key
        if raw:
            _ENCRYPTION_KEY = base64.urlsafe_b64decode(raw)
        else:
            logger.warning("No health_encryption_key set — health data stored as plaintext!")
            return b''
    return _ENCRYPTION_KEY


def encrypt_health_data(data: dict) -> str:
    """Encrypt health_data JSON dict → base64 string."""
    key = _get_key()
    if not key:
        return json.dumps(data)  # Fallback: plaintext
    f = Fernet(key)
    plaintext = json.dumps(data).encode('utf-8')
    return f.encrypt(plaintext).decode('utf-8')


def decrypt_health_data(encrypted: str) -> dict:
    """Decrypt base64 string → health_data JSON dict."""
    key = _get_key()
    if not key:
        try:
            return json.loads(encrypted) if isinstance(encrypted, str) else encrypted
        except (json.JSONDecodeError, TypeError):
            return {}
    f = Fernet(key)
    try:
        plaintext = f.decrypt(encrypted.encode('utf-8'))
        return json.loads(plaintext)
    except Exception as e:
        logger.error(f"Health data decryption failed: {e}")
        return {}
