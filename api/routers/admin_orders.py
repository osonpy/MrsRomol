"""
admin_orders.py — dashboard and order handling for admins.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query

from api import actions, notify
from api.auth import Admin
from api.catalog import LOW_STOCK
from api.constants import ORDER_STATUSES
from api.db import db, first, rpc, run, run_count
from api.errors import not_found, validation
from api.orders import load_order, shape_order
from api.schemas import AdminCancelRequest, AdvanceOrderRequest, OrderNotePatch, ReviewPaymentRequest

router = APIRouter(prefix="/admin", tags=["admin: orders"])

_TASHKENT = timezone(timedelta(hours=5))
_PAID = ("confirmed", "shipped", "delivered")


@router.get("/dashboard")
async def dashboard(admin: Admin) -> dict:
    today = datetime.now(_TASHKENT).replace(hour=0, minute=0, second=0, microsecond=0)
    todays = await run(
        db().table("orders").select("status, total").gte("created_at", today.isoformat())
    )
    open_orders = await run(
        db().table("orders").select("status")
        .in_("status", ["awaiting_payment", "payment_review", "confirmed"])
    )
    low = await run(
        db().table("product_variants")
        .select("id, color_uz, size, stock, product:products(id, name_uz)")
        .eq("is_active", True).lte("stock", LOW_STOCK).order("stock").limit(20)
    )
    counts = {s: 0 for s in ("awaiting_payment", "payment_review", "confirmed")}
    for o in open_orders:
        counts[o["status"]] += 1
    return {
        "today": {
            "orders": len(todays),
            "revenue": sum(o["total"] for o in todays if o["status"] in _PAID),
        },
        "to_review": counts["payment_review"],
        "to_ship": counts["confirmed"],
        "awaiting_payment": counts["awaiting_payment"],
        "low_stock": low,
    }


@router.get("/orders")
async def list_orders(
    admin: Admin,
    status: Optional[str] = None,
    q: Optional[str] = Query(default=None, max_length=32, description="order number or phone"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
) -> dict:
    query = db().table("orders").select(
        "id, number, status, cancel_reason, contact_name, contact_phone, region, delivery_method,"
        " total, created_at, expires_at, items:order_items(quantity)",
        count="exact",
    )
    if status:
        if status not in ORDER_STATUSES:
            raise validation("Unknown status")
        query = query.eq("status", status)
    if q and (term := q.strip().lstrip("#")):
        if term.isdigit() and len(term) <= 9:
            query = query.or_(f"number.eq.{term},contact_phone.ilike.*{term}*")
        else:
            digits = "".join(ch for ch in term if ch.isdigit())
            if not digits:
                raise validation("Search by order number or phone")
            query = query.ilike("contact_phone", f"*{digits}*")
    offset = (page - 1) * limit
    rows, total = await run_count(
        query.order("created_at", desc=True).range(offset, offset + limit - 1)
    )
    for r in rows:
        r["items_count"] = sum(i["quantity"] for i in r.pop("items"))
    return {"orders": rows, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.get("/orders/{order_id}")
async def get_order(order_id: UUID, admin: Admin) -> dict:
    return await shape_order(await load_order(str(order_id), admin=True), admin=True)


async def _notify_customer(background: BackgroundTasks, order: dict[str, Any], event: str, reason: str = "") -> None:
    c = order["customer"]
    background.add_task(notify.customer_order_update, c["telegram_id"], c["language"], order, event, reason)


@router.post("/payments/{payment_id}/review")
async def review_payment(
    payment_id: UUID, body: ReviewPaymentRequest, background: BackgroundTasks, admin: Admin,
) -> dict:
    if not body.approve and not body.reason.strip():
        raise validation("Reason is required when rejecting a payment")
    order = await actions.review_payment(str(payment_id), admin, body.approve, body.reason)
    background.add_task(actions.notify_review, order, body.approve, body.reason)
    return await shape_order(order, admin=True)


@router.post("/orders/{order_id}/advance")
async def advance_order(
    order_id: UUID, body: AdvanceOrderRequest, background: BackgroundTasks, admin: Admin,
) -> dict:
    await rpc("advance_order", {
        "p_order_id": str(order_id),
        "p_admin_id": admin["id"],
        "p_to": body.to,
        "p_tracking_number": body.tracking_number or None,
        "p_note": body.note,
    })
    order = await load_order(str(order_id), admin=True)
    await _notify_customer(background, order, body.to)
    return await shape_order(order, admin=True)


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: UUID, body: AdminCancelRequest, background: BackgroundTasks, admin: Admin,
) -> dict:
    await rpc("cancel_order", {
        "p_order_id": str(order_id), "p_actor": admin["id"], "p_reason": "by_admin", "p_note": body.note,
    })
    order = await load_order(str(order_id), admin=True)
    await _notify_customer(background, order, "by_admin", body.note)
    return await shape_order(order, admin=True)


@router.patch("/orders/{order_id}")
async def update_order_note(order_id: UUID, body: OrderNotePatch, admin: Admin) -> dict:
    if not await first(db().table("orders").select("id").eq("id", str(order_id))):
        raise not_found("Order not found")
    await run(db().table("orders").update({"admin_note": body.admin_note}).eq("id", str(order_id)))
    return await shape_order(await load_order(str(order_id), admin=True), admin=True)
