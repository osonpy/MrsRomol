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
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "http://localhost:5173")

# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_KEY: str = _require("SUPABASE_KEY")
