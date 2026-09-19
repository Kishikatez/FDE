"""Password hashing helpers for local employee and admin authentication."""

import hashlib
import hmac
import secrets


_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    """Hash a password with a per-user salt using PBKDF2-HMAC-SHA256."""

    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str | None) -> bool:
    """Verify a password hash without revealing whether the user exists."""

    if not encoded:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)
