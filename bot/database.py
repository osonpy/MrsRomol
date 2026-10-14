"""
database.py — ALL Supabase interactions live here.
Handlers must never call supabase client directly; go through these functions.
"""
from __future__ import annotations

import logging
from typing import Optional

from supabase import create_client, Client

from bot.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

# ── Singleton client ───────────────────────────────────────────────────────────
_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════

async def get_customer(telegram_id: str) -> Optional[dict]:
    """Return customer row by telegram_id."""
    try:
        res = (
            _supabase.table("customers")
            .select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_customer error: %s", e)
        return None
