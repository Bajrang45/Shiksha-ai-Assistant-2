import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"
_ITERATIONS = 260_000  # OWASP recommended minimum for PBKDF2-SHA256


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 (Python stdlib, no bcrypt)."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    # Store as "iterations:hex_salt:hex_key"
    return f"{_ITERATIONS}:{salt.hex()}:{key.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    try:
        iterations_str, salt_hex, key_hex = hashed_password.split(":")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, stored_key)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expires_at}, settings.secret_key, algorithm=ALGORITHM)
