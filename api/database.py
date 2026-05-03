from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from supabase import create_client, Client

from api.config import SUPABASE_URL, SUPABASE_KEY, BOT_TOKEN, RECEIPTS_BUCKET

logger = logging.getLogger(__name__)

_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── CUSTOMERS ──────────────────────────────────────────────────────────────────

async def get_customer(telegram_id: str) -> Optional[dict]:
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


async def upsert_customer(
    telegram_id: str,
    full_name: str,
    phone: str = "",
    language: str = "uz",
) -> Optional[dict]:
    try:
        existing = await get_customer(telegram_id)
        if existing:
            update_data: dict = {"full_name": full_name, "language": language}
            if phone:
                update_data["phone"] = phone
            res = (
                _supabase.table("customers")
                .update(update_data)
                .eq("telegram_id", telegram_id)
                .execute()
            )
            return res.data[0] if res.data else existing
        else:
            res = (
                _supabase.table("customers")
                .insert({"telegram_id": telegram_id, "full_name": full_name, "phone": phone, "language": language})
                .execute()
            )
            return res.data[0] if res.data else None
    except Exception as e:
        logger.error("upsert_customer error: %s", e)
        return None


async def update_customer_profile(
    telegram_id: str,
    phone: Optional[str] = None,
    language: Optional[str] = None,
    full_name: Optional[str] = None,
) -> Optional[dict]:
    try:
        update_data: dict = {}
        if phone is not None:
            update_data["phone"] = phone
        if language is not None:
            update_data["language"] = language
        if full_name is not None:
            update_data["full_name"] = full_name
        if not update_data:
            return await get_customer(telegram_id)
        res = (
            _supabase.table("customers")
            .update(update_data)
            .eq("telegram_id", telegram_id)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("update_customer_profile error: %s", e)
        return None


# ── PRODUCTS ───────────────────────────────────────────────────────────────────

async def get_all_products() -> list[dict]:
    try:
        res = (
            _supabase.table("products")
            .select("id, name, category, description, stock_qty, sell_price, image_file_id, metadata, is_active")
            .eq("is_active", True)
            .execute()
        )
        products = res.data or []
        # Sort by category then name
        products.sort(key=lambda p: (p.get("category") or "", p.get("name") or ""))
        return products
    except Exception as e:
        logger.error("get_all_products error: %s", e)
        return []


async def get_product_by_id(product_id: str) -> Optional[dict]:
    try:
        res = (
            _supabase.table("products")
            .select("id, name, category, description, stock_qty, cost_price, sell_price, wholesale_price, image_file_id, metadata, is_active")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_product_by_id error: %s", e)
        return None


async def get_telegram_file_url(file_id: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                params={"file_id": file_id},
            )
            data = resp.json()
            if not data.get("ok"):
                return None
            file_path = data["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    except Exception as e:
        logger.error("get_telegram_file_url error: %s", e)
        return None


async def decrement_stock(product_id: str, quantity: int) -> bool:
    try:
        product = await get_product_by_id(product_id)
        if not product or product["stock_qty"] < quantity:
            return False
        _supabase.table("products").update(
            {"stock_qty": product["stock_qty"] - quantity}
        ).eq("id", product_id).execute()
        return True
    except Exception as e:
        logger.error("decrement_stock error: %s", e)
        return False


# ── ORDERS ─────────────────────────────────────────────────────────────────────

async def create_order_with_items(
    customer_id: str,
    items: list[dict],
    delivery_type: str,
    address: str = "",
    notes: str = "",
) -> tuple[Optional[dict], Optional[str]]:
    try:
        enriched: list[dict] = []
        total_amount: float = 0.0

        for item in items:
            product = await get_product_by_id(item["product_id"])
            if not product:
                return None, f"Product {item['product_id']} not found"
            if not product.get("is_active"):
                return None, f"Product '{product['name']}' is no longer active"
            qty = item["quantity"]
            if product["stock_qty"] < qty:
                return None, f"OUT_OF_STOCK:{product['name']}:{qty}:{product['stock_qty']}"

            unit_price = float(product["sell_price"])
            enriched.append({
                "product_id": item["product_id"],
                "quantity": qty,
                "unit_price": unit_price,
                "product_name": product["name"],
            })
            total_amount += unit_price * qty

        order_res = (
            _supabase.table("orders")
            .insert({
                "customer_id": customer_id,
                "delivery_type": delivery_type,
                "address": address or "",
                "notes": notes or "",
                "total_amount": round(total_amount, 2),
                "source": "miniapp",
                "status": "pending",
            })
            .execute()
        )
        if not order_res.data:
            return None, "Failed to create order"

        order = order_res.data[0]
        order_id = order["id"]

        _supabase.table("order_items").insert([
            {"order_id": order_id, "product_id": e["product_id"],
             "quantity": e["quantity"], "unit_price": e["unit_price"]}
            for e in enriched
        ]).execute()

        for e in enriched:
            await decrement_stock(e["product_id"], e["quantity"])

        order["items"] = enriched
        return order, None

    except Exception as e:
        logger.error("create_order_with_items error: %s", e)
        return None, str(e)


async def get_customer_orders(customer_id: str, limit: int = 20) -> list[dict]:
    try:
        orders_res = (
            _supabase.table("orders")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        orders = orders_res.data or []

        for order in orders:
            oid = order["id"]
            items_res = (
                _supabase.table("order_items")
                .select("*, products(name, sell_price)")
                .eq("order_id", oid)
                .execute()
            )
            order["items"] = items_res.data or []

            pay_res = (
                _supabase.table("payments")
                .select("*")
                .eq("order_id", oid)
                .order("paid_at", desc=True)
                .limit(1)
                .execute()
            )
            order["payment"] = pay_res.data[0] if pay_res.data else None

        return orders
    except Exception as e:
        logger.error("get_customer_orders error: %s", e)
        return []


async def get_order_by_id(order_id: str) -> Optional[dict]:
    try:
        res = (
            _supabase.table("orders")
            .select("*, customers(telegram_id, full_name, language, phone)")
            .eq("id", order_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_order_by_id error: %s", e)
        return None


# ── PAYMENTS ───────────────────────────────────────────────────────────────────

async def create_payment(
    order_id: str,
    method: str,
    amount: float,
    receipt_file_id: str = "",
) -> Optional[dict]:
    try:
        res = (
            _supabase.table("payments")
            .insert({
                "order_id": order_id,
                "method": method,
                "amount": round(amount, 2),
                "receipt_file_id": receipt_file_id or None,
                "status": "pending_verification",
                "paid_at": datetime.now(timezone.utc).isoformat(),
            })
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("create_payment error: %s", e)
        return None


async def get_payment_by_id(payment_id: str) -> Optional[dict]:
    try:
        res = (
            _supabase.table("payments")
            .select("*")
            .eq("id", payment_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error("get_payment_by_id error: %s", e)
        return None


async def confirm_payment(payment_id: str) -> Optional[dict]:
    try:
        pay_res = (
            _supabase.table("payments")
            .update({"status": "confirmed"})
            .eq("id", payment_id)
            .execute()
        )
        if not pay_res.data:
            return None
        payment = pay_res.data[0]
        # Confirm order too
        _supabase.table("orders").update({"status": "confirmed"}).eq(
            "id", payment["order_id"]
        ).execute()
        return payment
    except Exception as e:
        logger.error("confirm_payment error: %s", e)
        return None


async def upload_receipt_to_storage(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> Optional[str]:
    try:
        path = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{filename}"
        _supabase.storage.from_(RECEIPTS_BUCKET).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        return _supabase.storage.from_(RECEIPTS_BUCKET).get_public_url(path)
    except Exception as e:
        logger.error("upload_receipt_to_storage error: %s", e)
        return None
