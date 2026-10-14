"""
catalog.py — shaping products for the shop and pricing a cart.

Customers never see exact stock or cost prices: only "in stock" and a
"few left" hint. Admin endpoints return raw rows instead.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from api.db import db, rpc, run
from api.errors import AppError
from api.storage import product_image_urls

LOW_STOCK = 3
NEW_DAYS = 14

PRODUCT_SELECT = (
    "id, category_id, name_uz, name_ru, description_uz, description_ru, price, size_chart, created_at,"
    " variants:product_variants(id, color_uz, color_ru, color_hex, size, stock, price_override, sort_order, is_active),"
    " images:product_images(id, color_uz, storage_path, sort_order)"
)


_APOSTROPHES = str.maketrans("", "", "'`ʻʼ‘’")
_UNSAFE = re.compile(r"[,()*%:\\\"\s]+")


def search_term(q: str) -> str:
    """
    Normalise a search query the same way products.search_text is built:
    lower-case, no apostrophes. PostgREST filter syntax characters are
    replaced with a wildcard so user input can't change the query.
    """
    return _UNSAFE.sub("*", q.lower().translate(_APOSTROPHES)).strip("*")


def _active_variants(p: dict[str, Any]) -> list[dict[str, Any]]:
    vs = [v for v in p.get("variants") or [] if v["is_active"]]
    return sorted(vs, key=lambda v: (v["sort_order"], v["color_uz"] or "", v["size"] or ""))


def _images(p: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": i["id"], "color_uz": i["color_uz"], **product_image_urls(i["storage_path"])}
        for i in sorted(p.get("images") or [], key=lambda i: i["sort_order"])
    ]


def _price(p: dict[str, Any], v: dict[str, Any]) -> int:
    return v["price_override"] if v["price_override"] is not None else p["price"]


def _is_new(p: dict[str, Any]) -> bool:
    created = datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
    return created > datetime.now(timezone.utc) - timedelta(days=NEW_DAYS)


def shape_product_card(p: dict[str, Any], favorite_ids: set[str] | None = None) -> dict[str, Any]:
    variants = _active_variants(p)
    prices = [_price(p, v) for v in variants] or [p["price"]]
    images = _images(p)
    colors: dict[str, dict[str, Any]] = {}
    for v in variants:
        if v["color_uz"] and v["color_uz"] not in colors:
            colors[v["color_uz"]] = {"uz": v["color_uz"], "ru": v["color_ru"], "hex": v["color_hex"]}
    sizes = list(dict.fromkeys(v["size"] for v in variants if v["size"]))
    return {
        "id": p["id"],
        "category_id": p["category_id"],
        "name_uz": p["name_uz"],
        "name_ru": p["name_ru"],
        "price": min(prices),
        "price_max": max(prices),
        "in_stock": any(v["stock"] > 0 for v in variants),
        "is_new": _is_new(p),
        "image": images[0] if images else None,
        "colors": list(colors.values()),
        "sizes": sizes,
        "is_favorite": p["id"] in (favorite_ids or set()),
    }


def shape_product_detail(p: dict[str, Any], is_favorite: bool = False) -> dict[str, Any]:
    card = shape_product_card(p, {p["id"]} if is_favorite else set())
    card.pop("image")
    return {
        **card,
        "description_uz": p["description_uz"],
        "description_ru": p["description_ru"],
        "size_chart": p["size_chart"],
        "images": _images(p),
        "variants": [
            {
                "id": v["id"],
                "color_uz": v["color_uz"],
                "color_ru": v["color_ru"],
                "color_hex": v["color_hex"],
                "size": v["size"],
                "price": _price(p, v),
                "in_stock": v["stock"] > 0,
                "low_stock": 0 < v["stock"] <= LOW_STOCK,
            }
            for v in _active_variants(p)
        ],
    }


async def quote_cart(
    customer_id: str, items: list[dict[str, Any]], promo_code: str | None
) -> dict[str, Any]:
    """
    Price a cart without changing anything: current prices, stock problems and
    the promo discount. The real order is priced again by create_order.
    """
    quantities: dict[str, int] = {}
    for it in items:
        key = str(it["variant_id"])
        quantities[key] = quantities.get(key, 0) + it["quantity"]

    rows = await run(
        db().table("product_variants")
        .select(
            "id, color_uz, color_ru, size, stock, price_override, is_active,"
            " product:products(id, name_uz, name_ru, price, is_active,"
            " images:product_images(color_uz, storage_path, sort_order))"
        )
        .in_("id", list(quantities))
    )
    by_id = {r["id"]: r for r in rows}

    lines, issues, subtotal = [], [], 0
    for variant_id, qty in quantities.items():
        v = by_id.get(variant_id)
        if v is None:
            issues.append({"variant_id": variant_id, "code": "VARIANT_NOT_FOUND"})
            continue
        p = v["product"]
        if not (v["is_active"] and p["is_active"]):
            issues.append({"variant_id": variant_id, "code": "PRODUCT_INACTIVE"})
            continue
        if v["stock"] < qty:
            issues.append({"variant_id": variant_id, "code": "OUT_OF_STOCK", "available": v["stock"]})
        price = _price(p, v)
        imgs = sorted(p.get("images") or [], key=lambda i: (i["color_uz"] != v["color_uz"], i["sort_order"]))
        line_qty = min(qty, v["stock"])
        subtotal += price * line_qty
        lines.append({
            "variant_id": variant_id,
            "product_id": p["id"],
            "name_uz": p["name_uz"],
            "name_ru": p["name_ru"],
            "color_uz": v["color_uz"],
            "color_ru": v["color_ru"],
            "size": v["size"],
            "unit_price": price,
            "quantity": qty,
            "available": v["stock"],
            "line_total": price * line_qty,
            "image": product_image_urls(imgs[0]["storage_path"]) if imgs else None,
        })

    promo: dict[str, Any] | None = None
    discount = 0
    if promo_code and promo_code.strip():
        try:
            res = await rpc("promo_discount", {
                "p_code": promo_code, "p_customer_id": customer_id, "p_subtotal": subtotal,
            })
            discount = int(res[0]["discount"]) if res else 0
            promo = {"code": promo_code.strip().upper(), "valid": True}
        except AppError as e:
            if not e.code.startswith("PROMO_"):
                raise
            promo = {"code": promo_code.strip().upper(), "valid": False, "error_code": e.code, "detail": e.detail}

    return {
        "lines": lines,
        "issues": issues,
        "subtotal": subtotal,
        "discount": discount,
        "total": subtotal - discount,
        "promo": promo,
    }
