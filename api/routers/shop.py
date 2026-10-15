"""
shop.py — endpoints for customers (the Mini App storefront).
"""
import logging
from typing import Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile

from api import notify
from api.auth import Customer
from api.catalog import PRODUCT_SELECT, quote_cart, search_term, shape_product_card, shape_product_detail
from api.constants import DELIVERY_METHODS, REGIONS
from api.db import db, first, rpc, run, run_count
from api.errors import AppError, not_found
from api.orders import load_order, shape_order
from api.schemas import CreateOrderRequest, ProfileUpdate, QuoteRequest
from api.storage import delete_receipt, receipt_signed_url, upload_receipt

logger = logging.getLogger(__name__)
router = APIRouter(tags=["shop"])

PROFILE_FIELDS = ("id", "telegram_id", "full_name", "phone", "language", "role", "notify_new_products")


def _profile(c: dict[str, Any]) -> dict[str, Any]:
    return {k: c[k] for k in PROFILE_FIELDS}


async def _settings() -> dict[str, Any]:
    rows = await run(db().table("settings").select("key, value"))
    return {r["key"]: r["value"] for r in rows}


# ── meta & profile ────────────────────────────────────────────────────────────

@router.get("/meta")
async def meta(customer: Customer) -> dict:
    """Everything the app needs at start-up besides the catalogue."""
    settings = await _settings()
    categories = await run(
        db().table("categories").select("id, slug, name_uz, name_ru")
        .eq("is_active", True).order("sort_order").order("name_uz")
    )
    return {
        "me": _profile(customer),
        "categories": categories,
        "regions": REGIONS,
        "delivery_methods": DELIVERY_METHODS,
        "reservation_minutes": settings.get("reservation_minutes", 30),
        "rules": {"uz": settings.get("rules_uz", ""), "ru": settings.get("rules_ru", "")},
    }


@router.get("/me")
async def get_me(customer: Customer) -> dict:
    return _profile(customer)


@router.patch("/me")
async def update_me(body: ProfileUpdate, customer: Customer) -> dict:
    data = body.model_dump(exclude_none=True)
    if not data:
        return _profile(customer)
    rows = await run(db().table("customers").update(data).eq("id", customer["id"]))
    return _profile(rows[0])


# ── catalogue ─────────────────────────────────────────────────────────────────



@router.get("/products")
async def list_products(
    customer: Customer,
    q: Optional[str] = Query(default=None, max_length=64),
    category_id: Optional[UUID] = None,
    min_price: Optional[int] = Query(default=None, ge=0),
    max_price: Optional[int] = Query(default=None, ge=0),
    size: Optional[str] = Query(default=None, max_length=20),
    color: Optional[str] = Query(default=None, max_length=50),
    sort: Literal["new", "price_asc", "price_desc"] = "new",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    select = PRODUCT_SELECT
    if size or color:
        select += ", vf:product_variants!inner(id)"
    query = db().table("products").select(select, count="exact").eq("is_active", True)

    if q and (term := search_term(q)):
        query = query.ilike("search_text", f"*{term}*")
    if category_id:
        query = query.eq("category_id", str(category_id))
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    if size or color:
        query = query.eq("vf.is_active", True).gt("vf.stock", 0)
        if size:
            query = query.eq("vf.size", size)
        if color:
            query = query.eq("vf.color_uz", color)

    if sort == "new":
        query = query.order("created_at", desc=True)
    else:
        query = query.order("price", desc=(sort == "price_desc")).order("created_at", desc=True)

    offset = (page - 1) * limit
    rows, total = await run_count(query.range(offset, offset + limit - 1))

    fav_ids: set[str] = set()
    if rows:
        favs = await run(
            db().table("favorites").select("product_id")
            .eq("customer_id", customer["id"]).in_("product_id", [r["id"] for r in rows])
        )
        fav_ids = {f["product_id"] for f in favs}

    return {
        "products": [shape_product_card(r, fav_ids) for r in rows],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/products/{product_id}")
async def get_product(product_id: UUID, customer: Customer) -> dict:
    p = await first(db().table("products").select(PRODUCT_SELECT).eq("id", str(product_id)).eq("is_active", True))
    if p is None:
        raise not_found("Product not found")
    fav = await first(
        db().table("favorites").select("product_id")
        .eq("customer_id", customer["id"]).eq("product_id", str(product_id))
    )
    return shape_product_detail(p, is_favorite=fav is not None)


# ── favorites ─────────────────────────────────────────────────────────────────

@router.get("/favorites")
async def list_favorites(customer: Customer) -> dict:
    rows = await run(
        db().table("favorites").select(f"created_at, product:products({PRODUCT_SELECT}, is_active)")
        .eq("customer_id", customer["id"]).order("created_at", desc=True)
    )
    products = [r["product"] for r in rows if r["product"] and r["product"]["is_active"]]
    ids = {p["id"] for p in products}
    return {"products": [shape_product_card(p, ids) for p in products]}


@router.put("/favorites/{product_id}", status_code=204)
async def add_favorite(product_id: UUID, customer: Customer) -> None:
    await run(
        db().table("favorites").upsert(
            {"customer_id": customer["id"], "product_id": str(product_id)},
            on_conflict="customer_id,product_id", ignore_duplicates=True,
        )
    )


@router.delete("/favorites/{product_id}", status_code=204)
async def remove_favorite(product_id: UUID, customer: Customer) -> None:
    await run(
        db().table("favorites").delete()
        .eq("customer_id", customer["id"]).eq("product_id", str(product_id))
    )


# ── cart & orders ─────────────────────────────────────────────────────────────

@router.post("/cart/quote")
async def cart_quote(body: QuoteRequest, customer: Customer) -> dict:
    return await quote_cart(customer["id"], [i.model_dump() for i in body.items], body.promo_code)


@router.post("/orders", status_code=201)
async def create_order(body: CreateOrderRequest, background: BackgroundTasks, customer: Customer) -> dict:
    created = await rpc("create_order", {
        "p_customer_id": customer["id"],
        "p_items": [{"variant_id": str(i.variant_id), "quantity": i.quantity} for i in body.items],
        "p_delivery": body.delivery.model_dump(),
        "p_promo_code": body.promo_code,
    })
    order = await load_order(created["id"])
    shaped = await shape_order(order)
    shaped["payment_cards"] = await _payment_cards()  # the app goes straight to payment

    # Remember contact details for the next checkout.
    profile: dict[str, Any] = {}
    if not customer["phone"]:
        profile["phone"] = body.delivery.contact_phone
    if not customer["full_name"]:
        profile["full_name"] = body.delivery.contact_name
    if profile:
        await run(db().table("customers").update(profile).eq("id", customer["id"]))

    minutes = (await _settings()).get("reservation_minutes", 30)
    background.add_task(notify.admin_new_order, order, order["items"])
    background.add_task(
        notify.customer_order_update, customer["telegram_id"], customer["language"],
        order, "awaiting_payment", minutes=minutes,
    )
    return shaped


@router.get("/orders")
async def list_orders(
    customer: Customer,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict:
    offset = (page - 1) * limit
    rows, total = await run_count(
        db().table("orders")
        .select(
            "id, number, status, cancel_reason, total, created_at, expires_at,"
            " items:order_items(product_name_uz, product_name_ru, quantity)",
            count="exact",
        )
        .eq("customer_id", customer["id"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    return {"orders": rows, "total": total, "page": page, "pages": (total + limit - 1) // limit}


async def _own_order(order_id: UUID, customer: dict[str, Any]) -> dict[str, Any]:
    order = await load_order(str(order_id))
    if order["customer_id"] != customer["id"]:
        raise not_found("Order not found")  # don't reveal other people's orders exist
    return order


@router.get("/orders/{order_id}")
async def get_order(order_id: UUID, customer: Customer) -> dict:
    order = await _own_order(order_id, customer)
    shaped = await shape_order(order)
    if order["status"] == "awaiting_payment":
        shaped["payment_cards"] = await _payment_cards()
    return shaped


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: UUID, customer: Customer) -> dict:
    await _own_order(order_id, customer)
    await rpc("cancel_order", {
        "p_order_id": str(order_id), "p_actor": customer["id"], "p_reason": "by_customer",
    })
    return await shape_order(await load_order(str(order_id)))


# ── payment ───────────────────────────────────────────────────────────────────

async def _payment_cards() -> list[dict[str, Any]]:
    return await run(
        db().table("payment_cards").select("id, card_number, holder_name, card_type")
        .eq("is_active", True).order("sort_order")
    )


@router.get("/payment-cards")
async def payment_cards(customer: Customer) -> dict:
    return {"cards": await _payment_cards()}


@router.post("/orders/{order_id}/payment", status_code=201)
async def submit_payment(
    order_id: UUID,
    background: BackgroundTasks,
    customer: Customer,
    receipt: UploadFile = File(...),
    card_id: Optional[UUID] = Form(default=None),
) -> dict:
    # Check before uploading, so nobody can fill storage through foreign orders.
    order = await _own_order(order_id, customer)
    if order["status"] != "awaiting_payment":
        raise AppError(409, "INVALID_TRANSITION", detail={"from": order["status"], "to": "payment_review"})

    data = await receipt.read(10 * 1024 * 1024 + 1)
    path = await upload_receipt(str(order_id), receipt.content_type or "", data)
    try:
        payment = await rpc("submit_payment", {
            "p_order_id": str(order_id),
            "p_customer_id": customer["id"],
            "p_card_id": str(card_id) if card_id else None,
            "p_receipt_path": path,
        })
    except AppError:
        await delete_receipt(path)
        raise

    order = await load_order(str(order_id))
    background.add_task(notify.admin_new_payment, order, payment["id"], await receipt_signed_url(path))
    background.add_task(
        notify.customer_order_update, customer["telegram_id"], customer["language"], order, "payment_review",
    )
    return await shape_order(order)
