import hashlib
import hmac
import json
import urllib.parse
from typing import Annotated

from fastapi import Header, HTTPException, Depends

from api.config import BOT_TOKEN, DEV_MODE

_MOCK_INIT_DATA = "mock_init_data_for_dev"
_MOCK_TELEGRAM_ID = "123456789"


def verify_telegram_init_data(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
) -> str:
    """
    FastAPI dependency: verifies Telegram WebApp initData HMAC-SHA256 signature.
    Returns the authenticated telegram_id as a string.

    Algorithm (per Telegram docs):
      secret_key = HMAC-SHA256(key="WebAppData", msg=BOT_TOKEN)
      data_check_string = sorted key=value lines joined by \\n (hash excluded)
      expected = HMAC-SHA256(key=secret_key, msg=data_check_string).hexdigest()
    """
    if not x_telegram_init_data:
        _unauthorized()

    if DEV_MODE and x_telegram_init_data == _MOCK_INIT_DATA:
        return _MOCK_TELEGRAM_ID

    try:
        parsed = dict(urllib.parse.parse_qsl(x_telegram_init_data, keep_blank_values=True))
    except Exception:
        _unauthorized()

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        _unauthorized()

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        _unauthorized()

    user_str = parsed.get("user", "{}")
    try:
        user = json.loads(user_str)
        telegram_id = str(user["id"])
    except (json.JSONDecodeError, KeyError, TypeError):
        _unauthorized()

    return telegram_id


def _unauthorized() -> None:
    raise HTTPException(
        status_code=401,
        detail={"error": "Unauthorized", "code": "INVALID_INIT_DATA"},
    )


TelegramUser = Annotated[str, Depends(verify_telegram_init_data)]
