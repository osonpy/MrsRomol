"""
config.py — loads all environment variables and exposes typed constants.
Never import os.environ directly in handlers; use this module instead.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Raise a clear error if a required env var is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"❌ Required environment variable '{key}' is not set. "
            "Check your .env file."
        )
    return value


# ── Telegram ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = _require("BOT_TOKEN")
ADMIN_GROUP_ID: int = int(_require("ADMIN_GROUP_ID"))
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "http://localhost:5173")

# ADMIN_USER_IDS: comma-separated personal Telegram user IDs that can use
# admin commands (/setphotos, /pending). Example: "123456789,987654321"
# If not set, falls back to ADMIN_GROUP_ID (works if ADMIN_GROUP_ID is a
# private chat / the admin's personal chat with the bot).
def _parse_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_USER_IDS", "")
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() or (part.startswith("-") and part[1:].isdigit()):
            ids.add(int(part))
    if not ids:  # fallback: treat ADMIN_GROUP_ID as the admin's personal chat
        ids.add(ADMIN_GROUP_ID)
    return ids

ADMIN_USER_IDS: set[int] = _parse_admin_ids()

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")

# ── Business logic ───────────────────────────────────────────────────────────
PAYMENT_CARD: str = _require("PAYMENT_CARD")

# ── Pagination ───────────────────────────────────────────────────────────────
PRODUCTS_PER_PAGE: int = 5

# ── Supported languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES: list[str] = ["uz", "ru", "en"]
DEFAULT_LANGUAGE: str = "uz"

# ── Order statuses ────────────────────────────────────────────────────────────
class OrderStatus:
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    SHIPPED   = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# ── Payment statuses ──────────────────────────────────────────────────────────
class PaymentStatus:
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED             = "verified"
    REJECTED             = "rejected"
