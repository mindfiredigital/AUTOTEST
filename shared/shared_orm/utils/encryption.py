"""
Field-level encryption utility for sensitive DB columns (e.g. LLM API keys).

Usage:
    from shared_orm.utils.encryption import encrypt_value, decrypt_value

    # Encrypt before storing to DB
    encrypted = encrypt_value(raw_api_key)

    # Decrypt after reading from DB
    raw = decrypt_value(encrypted)

Environment variable:
    FIELD_ENCRYPTION_KEY — 32-byte URL-safe base64 Fernet key.
    Generate with:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    If the env var is absent the module logs a warning and falls back to
    identity (no-op) behaviour so the app still runs in development without
    breaking existing plaintext rows.
"""

import logging
import os

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "")
_ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
_IS_PRODUCTION = _ENVIRONMENT == "production"
_fernet = None

if _ENCRYPTION_KEY:
    try:
        from cryptography.fernet import Fernet, InvalidToken
        _fernet = Fernet(_ENCRYPTION_KEY.encode())
    except Exception as e:
        msg = f"[ENCRYPTION] Invalid FIELD_ENCRYPTION_KEY: {e}"
        if _IS_PRODUCTION:
            raise RuntimeError(
                f"{msg} — Cannot start in production without valid encryption key."
            )
        logger.critical(f"{msg} — field-level encryption disabled (dev only).")
else:
    if _IS_PRODUCTION:
        raise RuntimeError(
            "[ENCRYPTION] FIELD_ENCRYPTION_KEY must be set in production. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        )
    logger.warning(
        "[ENCRYPTION] FIELD_ENCRYPTION_KEY not set — "
        "API keys are stored/read as plaintext. "
        "Set this variable in production (ENVIRONMENT=production)."
    )


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string value. Returns the encrypted string (Fernet token).
    If encryption is not configured, returns the original value unchanged.
    """
    if not plaintext:
        return plaintext
    if _fernet is None:
        return plaintext
    try:
        return _fernet.encrypt(plaintext.encode()).decode()
    except Exception as e:
        logger.error(f"[ENCRYPTION] encrypt_value failed: {e}")
        return plaintext


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted string. Falls back to returning the raw value
    if decryption fails (handles existing plaintext rows during migration).
    If encryption is not configured, returns the value unchanged.
    """
    if not ciphertext:
        return ciphertext
    if _fernet is None:
        return ciphertext
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except Exception:
        # Likely a plaintext value from before encryption was enabled
        logger.debug(
            "[ENCRYPTION] decrypt_value: could not decrypt — returning as plaintext "
            "(may be a legacy unencrypted row)"
        )
        return ciphertext
