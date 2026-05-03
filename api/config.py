import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


BOT_TOKEN: str = _require("BOT_TOKEN")
ADMIN_GROUP_ID: int = int(_require("ADMIN_GROUP_ID"))
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "http://localhost:5173")

# All chat IDs that receive admin notifications (group + personal IDs)
# Example: ADMIN_NOTIFY_IDS=-1001234567890,123456789
def _parse_notify_ids() -> list[int]:
    raw = os.getenv("ADMIN_NOTIFY_IDS", "")
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.append(int(part))
    return ids or [ADMIN_GROUP_ID]

ADMIN_NOTIFY_IDS: list[int] = _parse_notify_ids()

SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

# X-Admin-Key header value for admin/internal endpoints
ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", os.getenv("INTERNAL_SECRET", "change-me"))
INTERNAL_SECRET: str = ADMIN_SECRET_KEY  # backward-compat alias

_raw_origins = os.getenv("ALLOWED_ORIGINS", f"{MINI_APP_URL},http://localhost:5173")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

RECEIPTS_BUCKET: str = os.getenv("RECEIPTS_BUCKET", "receipts")
DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
