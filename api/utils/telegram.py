import hmac
import hashlib
import json
import os
import urllib.parse
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# In development, allow mock initData without real Telegram session
_DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
_MOCK_INIT_DATA = "mock_init_data_for_dev"

_DEV_USER = {
    "user": {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "uz",
    }
}


def verify_init_data(init_data: str, bot_token: str) -> dict:
    """
    Verify Telegram WebApp initData signature.
    Raises HTTP 401 if signature is invalid.
    Returns parsed dict of all fields (including decoded 'user' as dict).

    DEV MODE: if DEV_MODE=true env var is set, accepts 'mock_init_data_for_dev' without verification.
    Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    # ── Dev bypass ─────────────────────────────────────────────────────────────
    if _DEV_MODE and init_data == _MOCK_INIT_DATA:
        return _DEV_USER

    try:
        # Parse the query string
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed initData")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    # Build data-check-string: sorted key=value pairs joined by \n
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # expected = HMAC-SHA256(secret_key, data_check_string)
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    # Decode nested JSON fields
    if "user" in parsed:
        try:
            parsed["user"] = json.loads(parsed["user"])
        except Exception:
            pass

    return parsed


def extract_telegram_id(init_data_parsed: dict) -> Optional[str]:
    """Extract telegram user ID from parsed initData dict."""
    user = init_data_parsed.get("user")
    if isinstance(user, dict):
        uid = user.get("id")
        return str(uid) if uid else None
    return None


def extract_language(init_data_parsed: dict) -> str:
    """Extract language_code from Telegram user, defaulting to 'uz'."""
    user = init_data_parsed.get("user")
    if isinstance(user, dict):
        lang = user.get("language_code", "uz")
        return lang if lang in ("uz", "ru", "en") else "uz"
    return "uz"
