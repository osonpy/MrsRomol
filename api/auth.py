"""
auth.py — who is calling.

Every request from the Mini App carries Telegram WebApp initData in the
X-Telegram-Init-Data header. We verify its signature, then load (or create)
the matching customer row. Admin endpoints additionally check the role.
"""
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Annotated, Any

from fastapi import Depends, Header

from api.actions import ADMIN_ROLES, ensure_customer
from api.config import BOT_TOKEN, DEV_MODE, INIT_DATA_MAX_AGE
from api.errors import AppError, forbidden

_MOCK_INIT_DATA = "mock_init_data_for_dev"
_MOCK_USER = {"id": 123456789, "first_name": "Test", "last_name": "User", "language_code": "uz"}



def _unauthorized() -> AppError:
    return AppError(401, "INVALID_INIT_DATA", "Unauthorized")


def verify_init_data(init_data: str) -> dict[str, Any]:
    """
    Verify Telegram WebApp initData (HMAC-SHA256, per Telegram docs) and
    return the Telegram user dict.

      secret_key = HMAC-SHA256(key="WebAppData", msg=BOT_TOKEN)
      data_check_string = sorted key=value lines joined by \\n (hash excluded)
      expected = HMAC-SHA256(key=secret_key, msg=data_check_string).hexdigest()
    """
    if DEV_MODE and init_data == _MOCK_INIT_DATA:
        return dict(_MOCK_USER)

    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise _unauthorized()

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise _unauthorized()

    # A valid signature never expires on its own, so reject stale initData.
    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError:
        raise _unauthorized()
    if time.time() - auth_date > INIT_DATA_MAX_AGE:
        raise _unauthorized()

    try:
        user = json.loads(parsed.get("user", ""))
        int(user["id"])
    except (ValueError, KeyError, TypeError):
        raise _unauthorized()
    return user


def telegram_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
) -> dict[str, Any]:
    return verify_init_data(x_telegram_init_data)


async def current_customer(
    tg_user: Annotated[dict[str, Any], Depends(telegram_user)],
) -> dict[str, Any]:
    """Load the caller's customer row, creating it on first visit."""
    return await ensure_customer(tg_user)


async def current_admin(
    customer: Annotated[dict[str, Any], Depends(current_customer)],
) -> dict[str, Any]:
    if customer["role"] not in ADMIN_ROLES:
        raise forbidden("Admin access required")
    return customer


async def current_super_admin(
    customer: Annotated[dict[str, Any], Depends(current_customer)],
) -> dict[str, Any]:
    if customer["role"] != "super_admin":
        raise forbidden("Super admin access required")
    return customer


Customer = Annotated[dict[str, Any], Depends(current_customer)]
Admin = Annotated[dict[str, Any], Depends(current_admin)]
SuperAdmin = Annotated[dict[str, Any], Depends(current_super_admin)]
