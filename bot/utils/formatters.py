"""
formatters.py — pure formatting helpers.
No DB calls, no bot logic — only string transformations.
"""
from __future__ import annotations

import math
from datetime import datetime

from bot.config import PRODUCTS_PER_PAGE


def format_price(amount: float | int) -> str:
    """Format a numeric price with thousands separator: 1250000 → '1 250 000'"""
    return f"{int(amount):,}".replace(",", " ")


def format_date(dt_str: str) -> str:
    """
    Parse an ISO-8601 datetime string from Supabase and return a human-readable date.
    Example: '2024-03-15T10:30:00+00:00' → '15.03.2024 10:30'
    """
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return dt_str  # Return raw string if parsing fails


def total_pages(total_count: int) -> int:
    """Calculate total pages given a total item count and the global page size."""
    if total_count == 0:
        return 1
    return math.ceil(total_count / PRODUCTS_PER_PAGE)


def format_order_items_for_admin(items: list[dict]) -> str:
    """
    Format a list of order item dicts into a multi-line string for admin notification.
    Each item dict should have keys: product_name, quantity, unit_price.
    """
    lines = []
    for item in items:
        name  = item.get("product_name", "—")
        qty   = item.get("quantity", 0)
        price = format_price(item.get("unit_price", 0))
        lines.append(f"  • {name} × {qty} шт. — {price} UZS")
    return "\n".join(lines) if lines else "  —"


def short_uuid(uuid_str: str) -> str:
    """Return the last 8 characters of a UUID for compact display."""
    return uuid_str[-8:].upper() if uuid_str else "—"
