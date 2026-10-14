"""
orders.py — loading and shaping orders (shared by shop and admin routers).
"""
from typing import Any

from api.db import db, first
from api.errors import not_found
from api.storage import product_image_urls, receipt_signed_url

ORDER_SELECT = (
    "*,"
    " items:order_items(*, product:products(images:product_images(storage_path, sort_order, color_uz))),"
    " payments(id, status, amount, receipt_path, reject_reason, created_at, reviewed_at,"
    "  card:payment_cards(card_type, card_number, holder_name)),"
    " history:order_status_history(id, from_status, to_status, note, created_at)"
)
ADMIN_ORDER_SELECT = ORDER_SELECT + ", customer:customers(id, telegram_id, full_name, phone, language)"


async def load_order(order_id: str, admin: bool = False) -> dict[str, Any]:
    order = await first(
        db().table("orders").select(ADMIN_ORDER_SELECT if admin else ORDER_SELECT).eq("id", order_id)
    )
    if order is None:
        raise not_found("Order not found")
    return order


def _item_image(item: dict[str, Any]) -> dict[str, str] | None:
    images = (item.get("product") or {}).get("images") or []
    images = sorted(images, key=lambda i: (i["color_uz"] != item["color_uz"], i["sort_order"]))
    return product_image_urls(images[0]["storage_path"]) if images else None


async def shape_order(order: dict[str, Any], admin: bool = False) -> dict[str, Any]:
    items = [
        {
            "id": it["id"],
            "variant_id": it["variant_id"],
            "product_id": it["product_id"],
            "name_uz": it["product_name_uz"],
            "name_ru": it["product_name_ru"],
            "color_uz": it["color_uz"],
            "color_ru": it["color_ru"],
            "size": it["size"],
            "unit_price": it["unit_price"],
            "quantity": it["quantity"],
            "line_total": it["unit_price"] * it["quantity"],
            "image": _item_image(it),
        }
        for it in order.get("items") or []
    ]
    payments = sorted(order.get("payments") or [], key=lambda p: p["created_at"], reverse=True)
    payment = None
    if payments:
        p = payments[0]
        payment = {
            "id": p["id"],
            "status": p["status"],
            "amount": p["amount"],
            "reject_reason": p["reject_reason"],
            "created_at": p["created_at"],
            "reviewed_at": p["reviewed_at"],
            "card": p["card"],
        }
        if admin:
            payment["receipt_url"] = await receipt_signed_url(p["receipt_path"])

    shaped = {
        "id": order["id"],
        "number": order["number"],
        "status": order["status"],
        "cancel_reason": order["cancel_reason"],
        "contact_name": order["contact_name"],
        "contact_phone": order["contact_phone"],
        "region": order["region"],
        "district": order["district"],
        "address": order["address"],
        "location_lat": order["location_lat"],
        "location_lng": order["location_lng"],
        "delivery_method": order["delivery_method"],
        "tracking_number": order["tracking_number"],
        "customer_note": order["customer_note"],
        "subtotal": order["subtotal"],
        "discount": order["discount"],
        "total": order["total"],
        "expires_at": order["expires_at"],
        "created_at": order["created_at"],
        "items": items,
        "payment": payment,
        "history": [
            {k: h[k] for k in ("from_status", "to_status", "note", "created_at")}
            for h in sorted(order.get("history") or [], key=lambda h: h["id"])
        ],
    }
    if admin:
        shaped["admin_note"] = order["admin_note"]
        shaped["customer"] = order.get("customer")
    return shaped
