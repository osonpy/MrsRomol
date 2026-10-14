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


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════

async def get_order_by_id(order_id: str) -> Optional[dict]:
    """Return a single order row."""
    try:
        res = (
            _supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_order_by_id error: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════

async def get_pending_payments() -> list[dict]:
    """
    Return all payments with status='pending_verification', ordered oldest first.
    Used by admin /pending command to review unprocessed receipts.
    """
    try:
        res = (
            _supabase.table("payments")
            .select("*")
            .eq("status", "pending_verification")
            .order("paid_at")
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error("get_pending_payments error: %s", e)
        return []


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ACTIONS
# ══════════════════════════════════════════════════════════════════════════════

async def update_order_status(order_id: str, status: str) -> bool:
    """Update the status column of an order row."""
    try:
        _supabase.table("orders").update({"status": status}).eq(
            "id", order_id
        ).execute()
        return True
    except Exception as e:
        logger.error("update_order_status error: %s", e)
        return False


async def update_payment_status(order_id: str, status: str) -> bool:
    """Update payment status for all payments belonging to an order."""
    try:
        _supabase.table("payments").update({"status": status}).eq(
            "order_id", order_id
        ).execute()
        return True
    except Exception as e:
        logger.error("update_payment_status error: %s", e)
        return False


async def get_customer_by_order_id(order_id: str) -> Optional[dict]:
    """
    Resolve the customer who placed an order.
    Used by admin callbacks to find the customer's telegram_id for notifications.
    """
    try:
        order = await get_order_by_id(order_id)
        if not order:
            return None
        res = (
            _supabase.table("customers")
            .select("*")
            .eq("id", order["customer_id"])
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_customer_by_order_id error: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT IMAGES
# ══════════════════════════════════════════════════════════════════════════════

MAX_PRODUCT_IMAGES = 3


async def get_product_images(product_id: str) -> list[dict]:
    """
    Return all images for a product, ordered by sort_order.
    Each dict has keys: id, product_id, file_id, sort_order.
    """
    try:
        res = (
            _supabase.table("product_images")
            .select("*")
            .eq("product_id", product_id)
            .order("sort_order")
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error("get_product_images error: %s", e)
        return []


async def add_product_image(product_id: str, file_id: str) -> Optional[dict]:
    """
    Append a new image to a product (max 3 enforced here).
    Returns the inserted row, or None if limit reached or DB error.
    """
    try:
        existing = await get_product_images(product_id)
        if len(existing) >= MAX_PRODUCT_IMAGES:
            return None  # Caller should tell admin the limit is reached

        sort_order = len(existing)  # 0, 1, 2
        res = (
            _supabase.table("product_images")
            .insert(
                {
                    "product_id": product_id,
                    "file_id": file_id,
                    "sort_order": sort_order,
                }
            )
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("add_product_image error: %s", e)
        return None


async def delete_product_images(product_id: str) -> bool:
    """Remove ALL images for a product (used when admin resets photos)."""
    try:
        _supabase.table("product_images").delete().eq(
            "product_id", product_id
        ).execute()
        return True
    except Exception as e:
        logger.error("delete_product_images error: %s", e)
        return False


async def get_all_active_products_simple() -> list[dict]:
    """Return id + name for all active products (for admin product picker)."""
    try:
        res = (
            _supabase.table("products")
            .select("id, name, category")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error("get_all_active_products_simple error: %s", e)
        return []
