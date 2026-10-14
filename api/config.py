import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


def _int_list(key: str) -> list[int]:
    ids: list[int] = []
    for part in os.getenv(key, "").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.append(int(part))
    return ids


BOT_TOKEN: str = _require("BOT_TOKEN")
ADMIN_GROUP_ID: int = int(_require("ADMIN_GROUP_ID"))
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "http://localhost:5173").rstrip("/")
# Mini App direct link from BotFather (/newapp), e.g. https://t.me/MisrRomolBot/shop.
# Used for "open" buttons in group chats, where web_app buttons are not allowed.
MINI_APP_LINK: str = os.getenv("MINI_APP_LINK", "").rstrip("/")

# All chat IDs that receive admin notifications (group + personal IDs)
# Example: ADMIN_NOTIFY_IDS=-1001234567890,123456789
ADMIN_NOTIFY_IDS: list[int] = _int_list("ADMIN_NOTIFY_IDS") or [ADMIN_GROUP_ID]

# Telegram user IDs that always get the super_admin role (the shop owner).
# Other admins are appointed by a super_admin through the admin API.
SUPER_ADMIN_IDS: set[int] = set(_int_list("SUPER_ADMIN_IDS"))

SUPABASE_URL: str = _require("SUPABASE_URL").rstrip("/")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

PRODUCT_IMAGES_BUCKET = "product-images"
RECEIPTS_BUCKET = "receipts"

_raw_origins = os.getenv("ALLOWED_ORIGINS", f"{MINI_APP_URL},http://localhost:5173")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"

# How long a Telegram initData signature stays valid (seconds). Limits replay
# of a leaked initData string.
INIT_DATA_MAX_AGE: int = int(os.getenv("INIT_DATA_MAX_AGE", str(24 * 60 * 60)))

# How often unpaid orders are checked for an expired payment timer (seconds).
EXPIRY_CHECK_INTERVAL: int = int(os.getenv("EXPIRY_CHECK_INTERVAL", "60"))
