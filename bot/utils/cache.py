"""
utils/cache.py — In-memory TTL cache for customer data.

Problem solved:
  Every handler called get_customer() → 1 Supabase HTTP request per message
  = 600-1500ms latency per interaction → bot feels slow → Telegram retries
  updates → duplicate messages.

Solution:
  Cache customer dicts by telegram_id with a 5-minute TTL.
  On language change: invalidate the cache entry immediately.

Uses cachetools.TTLCache (already in requirements via supabase dependency).
Thread-safety is handled by asyncio single-thread model — no locks needed.
"""
from __future__ import annotations

from cachetools import TTLCache

# Max 5 000 customers cached, each entry expires after 5 minutes
_customer_cache: TTLCache = TTLCache(maxsize=5_000, ttl=300)


def cache_customer(telegram_id: str, customer: dict) -> None:
    """Store a customer dict in cache."""
    _customer_cache[telegram_id] = customer


def get_cached_customer(telegram_id: str) -> dict | None:
    """Return cached customer or None if missing/expired."""
    return _customer_cache.get(telegram_id)


def invalidate_customer(telegram_id: str) -> None:
    """Remove customer from cache (call after language change or profile update)."""
    _customer_cache.pop(telegram_id, None)
