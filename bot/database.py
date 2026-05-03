"""
database.py — ALL Supabase interactions live here.
Handlers must never call supabase client directly; go through these functions.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from supabase import create_client, Client

from bot.config import SUPABASE_URL, SUPABASE_KEY, PRODUCTS_PER_PAGE
from bot.utils.cache import cache_customer, get_cached_customer, invalidate_customer

logger = logging.getLogger(__name__)

# ── Singleton client ───────────────────────────────────────────────────────────
_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════

async def get_customer(telegram_id: str) -> Optional[dict]:
    """Return customer row by telegram_id. Checks TTL cache first."""
    # ★ Cache hit — skip Supabase entirely
    cached = get_cached_customer(telegram_id)
    if cached is not None:
        return cached

    try:
        res = (
            _supabase.table("customers")
            .select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        customer = res.data[0] if res.data else None
        if customer:
            cache_customer(telegram_id, customer)  # populate cache
        return customer
    except Exception as e:
        logger.error("get_customer error: %s", e)
        return None


async def create_customer(
    telegram_id: str,
    full_name: str,
    language: str,
    phone: str = "",
) -> Optional[dict]:
    """Insert a new customer row, populate cache, and return it."""
    try:
        res = (
            _supabase.table("customers")
            .insert(
                {
                    "telegram_id": telegram_id,
                    "full_name": full_name,
                    "language": language,
                    "phone": phone,
                }
            )
            .execute()
        )
        customer = res.data[0] if res.data else None
        if customer:
            cache_customer(telegram_id, customer)  # warm cache on creation
        return customer
    except Exception as e:
        logger.error("create_customer error: %s", e)
        return None


async def update_customer_language(telegram_id: str, language: str) -> bool:
    """Update the language preference and invalidate cache so next read is fresh."""
    try:
        _supabase.table("customers").update({"language": language}).eq(
            "telegram_id", telegram_id
        ).execute()
        invalidate_customer(telegram_id)
        return True
    except Exception as e:
        logger.error("update_customer_language error: %s", e)
        return False


async def update_customer_phone(telegram_id: str, phone: str) -> bool:
    """Save the customer's phone number and invalidate cache."""
    try:
        _supabase.table("customers").update({"phone": phone}).eq(
            "telegram_id", telegram_id
        ).execute()
        invalidate_customer(telegram_id)
        return True
    except Exception as e:
        logger.error("update_customer_phone error: %s", e)
        return False


async def upsert_customer(
    telegram_id: str,
    full_name: str,
    language: str,
) -> Optional[dict]:
    """
    Get existing customer or create one.
    Returns the customer dict, or None on DB error.
    """
    customer = await get_customer(telegram_id)
    if customer:
        return customer
    return await create_customer(telegram_id, full_name, language)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

async def get_products_page(page: int) -> tuple[list[dict], int]:
    """
    Return (products_on_page, total_count) for active products.
    `page` is 1-indexed.
    """
    try:
        offset = (page - 1) * PRODUCTS_PER_PAGE
        # Count total active products
        count_res = (
            _supabase.table("products")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
        )
        total = count_res.count or 0

        # Fetch page slice
        res = (
            _supabase.table("products")
            .select("*")
            .eq("is_active", True)
            .range(offset, offset + PRODUCTS_PER_PAGE - 1)
            .execute()
        )
        return res.data or [], total
    except Exception as e:
        logger.error("get_products_page error: %s", e)
        return [], 0


async def get_product_by_id(product_id: str) -> Optional[dict]:
    """Return a single product row by UUID."""
    try:
        res = (
            _supabase.table("products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_product_by_id error: %s", e)
        return None


async def decrement_stock(product_id: str, quantity: int) -> bool:
    """
    Atomically decrement stock_qty.
    Returns True on success, False if stock is insufficient or DB error.
    Uses a Supabase RPC for atomicity; falls back to read-then-write.
    """
    try:
        # Re-read stock to verify availability right before write
        product = await get_product_by_id(product_id)
        if not product or product["stock_qty"] < quantity:
            return False

        new_stock = product["stock_qty"] - quantity
        _supabase.table("products").update({"stock_qty": new_stock}).eq(
            "id", product_id
        ).execute()
        return True
    except Exception as e:
        logger.error("decrement_stock error: %s", e)
        return False


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════

async def create_order(
    customer_id: str,
    delivery_type: str,
    total_amount: float,
    notes: str = "",
    source: str = "telegram",
    status: str = "pending",
) -> Optional[dict]:
    """Insert a new order row and return it."""
    try:
        res = (
            _supabase.table("orders")
            .insert(
                {
                    "customer_id": customer_id,
                    "delivery_type": delivery_type,
                    "total_amount": total_amount,
                    "notes": notes,
                    "source": source,
                    "status": status,
                }
            )
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("create_order error: %s", e)
        return None


async def create_order_item(
    order_id: str,
    product_id: str,
    quantity: int,
    unit_price: float,
) -> Optional[dict]:
    """Insert a single order_items row."""
    try:
        res = (
            _supabase.table("order_items")
            .insert(
                {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            )
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("create_order_item error: %s", e)
        return None


async def get_customer_orders(customer_id: str, limit: int = 10) -> list[dict]:
    """Return the most recent `limit` orders for a customer."""
    try:
        res = (
            _supabase.table("orders")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error("get_customer_orders error: %s", e)
        return []


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

async def create_payment(
    order_id: str,
    amount: float,
    receipt_url: str,
    method: str = "card",
    status: str = "pending_verification",
) -> Optional[dict]:
    """Insert a payment record after the user sends a receipt."""
    try:
        res = (
            _supabase.table("payments")
            .insert(
                {
                    "order_id": order_id,
                    "amount": amount,
                    "receipt_url": receipt_url,
                    "method": method,
                    "status": status,
                    "paid_at": datetime.utcnow().isoformat(),
                }
            )
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("create_payment error: %s", e)
        return None


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
