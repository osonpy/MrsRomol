"""
admin_catalog.py — categories, products, variants and photos.
"""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile

from api import notify
from api.auth import Admin
from api.catalog import search_term
from api.db import db, first, run, run_count
from api.errors import AppError, not_found, validation
from api.schemas import (
    CategoryIn, CategoryPatch, ImageOrder, ImagePatch, ProductIn, ProductPatch, VariantIn, VariantPatch,
)
from api.storage import MAX_PRODUCT_IMAGE_BYTES, delete_product_images, product_image_urls, upload_product_image

router = APIRouter(prefix="/admin", tags=["admin: catalogue"])

MAX_IMAGES = 5
ADMIN_PRODUCT_SELECT = (
    "*, variants:product_variants(*), images:product_images(id, color_uz, storage_path, sort_order)"
)


def _shape(p: dict[str, Any]) -> dict[str, Any]:
    p["variants"] = sorted(p.get("variants") or [], key=lambda v: (v["sort_order"], v["color_uz"] or "", v["size"] or ""))
    p["images"] = [
        {"id": i["id"], "color_uz": i["color_uz"], "sort_order": i["sort_order"], **product_image_urls(i["storage_path"])}
        for i in sorted(p.get("images") or [], key=lambda i: i["sort_order"])
    ]
    p["total_stock"] = sum(v["stock"] for v in p["variants"])
    return p


async def _load(product_id: str) -> dict[str, Any]:
    p = await first(db().table("products").select(ADMIN_PRODUCT_SELECT).eq("id", product_id))
    if p is None:
        raise not_found("Product not found")
    return _shape(p)


def _dump(model: Any) -> dict[str, Any]:
    """Model → DB row: only fields that were sent; UUIDs as strings."""
    data = model.model_dump(exclude_unset=True, mode="json")
    if not data:
        raise validation("Nothing to update")
    return data


# ── categories ────────────────────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(admin: Admin) -> dict:
    return {"categories": await run(db().table("categories").select("*").order("sort_order").order("name_uz"))}


@router.post("/categories", status_code=201)
async def create_category(body: CategoryIn, admin: Admin) -> dict:
    return (await run(db().table("categories").insert(body.model_dump(mode="json"))))[0]


@router.patch("/categories/{category_id}")
async def update_category(category_id: UUID, body: CategoryPatch, admin: Admin) -> dict:
    rows = await run(db().table("categories").update(_dump(body)).eq("id", str(category_id)))
    if not rows:
        raise not_found("Category not found")
    return rows[0]


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: UUID, admin: Admin) -> None:
    # Products keep existing; their category becomes empty (on delete set null).
    await run(db().table("categories").delete().eq("id", str(category_id)))


# ── products ──────────────────────────────────────────────────────────────────

@router.get("/products")
async def list_products(
    admin: Admin,
    q: Optional[str] = Query(default=None, max_length=64),
    category_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
) -> dict:
    query = db().table("products").select(ADMIN_PRODUCT_SELECT, count="exact")
    if q and (term := search_term(q)):
        query = query.ilike("search_text", f"*{term}*")
    if category_id:
        query = query.eq("category_id", str(category_id))
    if is_active is not None:
        query = query.eq("is_active", is_active)
    offset = (page - 1) * limit
    rows, total = await run_count(query.order("created_at", desc=True).range(offset, offset + limit - 1))
    return {"products": [_shape(r) for r in rows], "total": total, "page": page,
            "pages": (total + limit - 1) // limit}


@router.get("/products/{product_id}")
async def get_product(product_id: UUID, admin: Admin) -> dict:
    return await _load(str(product_id))


@router.post("/products", status_code=201)
async def create_product(body: ProductIn, admin: Admin) -> dict:
    row = (await run(db().table("products").insert(body.model_dump(mode="json"))))[0]
    return await _load(row["id"])


@router.patch("/products/{product_id}")
async def update_product(product_id: UUID, body: ProductPatch, admin: Admin) -> dict:
    rows = await run(db().table("products").update(_dump(body)).eq("id", str(product_id)))
    if not rows:
        raise not_found("Product not found")
    return await _load(str(product_id))


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: UUID, admin: Admin) -> None:
    """
    Delete for good. Past orders are unaffected (they keep their own copy of
    name and price). To just hide a product, PATCH is_active=false instead.
    """
    p = await _load(str(product_id))
    paths = await run(db().table("product_images").select("storage_path").eq("product_id", p["id"]))
    await run(db().table("products").delete().eq("id", p["id"]))
    await delete_product_images([r["storage_path"] for r in paths])


# ── variants ──────────────────────────────────────────────────────────────────

@router.post("/products/{product_id}/variants", status_code=201)
async def create_variant(product_id: UUID, body: VariantIn, admin: Admin) -> dict:
    await _load(str(product_id))
    await run(db().table("product_variants").insert({**body.model_dump(mode="json"), "product_id": str(product_id)}))
    return await _load(str(product_id))


@router.patch("/variants/{variant_id}")
async def update_variant(variant_id: UUID, body: VariantPatch, admin: Admin) -> dict:
    rows = await run(db().table("product_variants").update(_dump(body)).eq("id", str(variant_id)))
    if not rows:
        raise not_found("Variant not found")
    return await _load(rows[0]["product_id"])


@router.delete("/variants/{variant_id}", status_code=204)
async def delete_variant(variant_id: UUID, admin: Admin) -> None:
    await run(db().table("product_variants").delete().eq("id", str(variant_id)))


# ── images ────────────────────────────────────────────────────────────────────

@router.post("/products/{product_id}/images", status_code=201)
async def upload_images(
    product_id: UUID,
    admin: Admin,
    files: list[UploadFile] = File(...),
    color_uz: Optional[str] = Form(default=None, max_length=50),
) -> dict:
    p = await _load(str(product_id))
    if len(p["images"]) + len(files) > MAX_IMAGES:
        raise AppError(409, "TOO_MANY_IMAGES", f"A product can have at most {MAX_IMAGES} photos",
                       {"max": MAX_IMAGES, "current": len(p["images"])})
    next_order = max((i["sort_order"] for i in p["images"]), default=-1) + 1
    for n, f in enumerate(files):
        path = await upload_product_image(p["id"], await f.read(MAX_PRODUCT_IMAGE_BYTES + 1))
        await run(db().table("product_images").insert({
            "product_id": p["id"], "storage_path": path, "sort_order": next_order + n,
            "color_uz": color_uz or None,
        }))
    return await _load(p["id"])


@router.patch("/images/{image_id}")
async def update_image(image_id: UUID, body: ImagePatch, admin: Admin) -> dict:
    rows = await run(
        db().table("product_images").update({"color_uz": body.color_uz or None}).eq("id", str(image_id))
    )
    if not rows:
        raise not_found("Image not found")
    return await _load(rows[0]["product_id"])


@router.put("/products/{product_id}/images/order")
async def reorder_images(product_id: UUID, body: ImageOrder, admin: Admin) -> dict:
    p = await _load(str(product_id))
    current = {i["id"] for i in p["images"]}
    wanted = [str(i) for i in body.image_ids]
    if set(wanted) != current or len(wanted) != len(current):
        raise validation("image_ids must list every photo of this product exactly once")
    for n, image_id in enumerate(wanted):
        await run(db().table("product_images").update({"sort_order": n}).eq("id", image_id))
    return await _load(p["id"])


@router.delete("/images/{image_id}", status_code=204)
async def delete_image(image_id: UUID, admin: Admin) -> None:
    rows = await run(db().table("product_images").delete().eq("id", str(image_id)))
    await delete_product_images([r["storage_path"] for r in rows])


# ── announcements ─────────────────────────────────────────────────────────────

async def _announce(product: dict[str, Any], image_url: str, price: int) -> None:
    subscribers = await run(
        db().table("customers").select("id, telegram_id, language").eq("notify_new_products", True)
    )
    blocked = await notify.announce_product(product, image_url, price, subscribers)
    if blocked:  # they blocked the bot: stop trying
        await run(db().table("customers").update({"notify_new_products": False}).in_("id", blocked))


@router.post("/products/{product_id}/announce")
async def announce_product(product_id: UUID, background: BackgroundTasks, admin: Admin) -> dict:
    """Send a published product to everyone subscribed to new arrivals — once."""
    p = await _load(str(product_id))
    in_stock = [v for v in p["variants"] if v["is_active"] and v["stock"] > 0]
    if not p["is_active"]:
        raise AppError(409, "NOT_PUBLISHED", "Publish the product first")
    if not p["images"]:
        raise AppError(409, "NO_IMAGE", "Add a photo first")
    if not in_stock:
        raise AppError(409, "OUT_OF_STOCK", "Nothing in stock")

    # Claim the announcement atomically: a double tap can't send twice.
    claimed = await run(
        db().table("products").update({"announced_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", p["id"]).is_("announced_at", "null")
    )
    if not claimed:
        raise AppError(409, "ALREADY_ANNOUNCED", "Already sent to subscribers")

    count = await run_count(
        db().table("customers").select("id", count="exact").eq("notify_new_products", True).limit(1)
    )
    price = min(v["price_override"] if v["price_override"] is not None else p["price"] for v in in_stock)
    background.add_task(_announce, p, p["images"][0]["url"], price)
    return {"recipients": count[1], "announced_at": claimed[0]["announced_at"]}
