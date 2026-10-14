"""
admin_settings.py — promo codes (admins), payment cards, shop settings and
staff roles (super_admin only).
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query

from api.auth import Admin, SuperAdmin
from api.db import db, first, run
from api.errors import forbidden, not_found, validation
from api.schemas import CardIn, CardPatch, PromoIn, PromoPatch, SettingsPatch, StaffRoleRequest

router = APIRouter(prefix="/admin", tags=["admin: settings"])


# ── promo codes ───────────────────────────────────────────────────────────────

@router.get("/promo-codes")
async def list_promo_codes(admin: Admin) -> dict:
    return {"promo_codes": await run(db().table("promo_codes").select("*").order("created_at", desc=True))}


@router.post("/promo-codes", status_code=201)
async def create_promo_code(body: PromoIn, admin: Admin) -> dict:
    return (await run(db().table("promo_codes").insert(body.model_dump(mode="json"))))[0]


@router.patch("/promo-codes/{promo_id}")
async def update_promo_code(promo_id: UUID, body: PromoPatch, admin: Admin) -> dict:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise validation("Nothing to update")
    rows = await run(db().table("promo_codes").update(data).eq("id", str(promo_id)))
    if not rows:
        raise not_found("Promo code not found")
    return rows[0]


# ── payment cards ─────────────────────────────────────────────────────────────

@router.get("/payment-cards")
async def list_cards(admin: Admin) -> dict:
    return {"cards": await run(db().table("payment_cards").select("*").order("sort_order"))}


@router.post("/payment-cards", status_code=201)
async def create_card(body: CardIn, admin: SuperAdmin) -> dict:
    return (await run(db().table("payment_cards").insert(body.model_dump())))[0]


@router.patch("/payment-cards/{card_id}")
async def update_card(card_id: UUID, body: CardPatch, admin: SuperAdmin) -> dict:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise validation("Nothing to update")
    rows = await run(db().table("payment_cards").update(data).eq("id", str(card_id)))
    if not rows:
        raise not_found("Card not found")
    return rows[0]


@router.delete("/payment-cards/{card_id}", status_code=204)
async def delete_card(card_id: UUID, admin: SuperAdmin) -> None:
    # Past payments keep working: payments.card_id becomes null.
    await run(db().table("payment_cards").delete().eq("id", str(card_id)))


# ── settings ──────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings(admin: Admin) -> dict:
    rows = await run(db().table("settings").select("key, value"))
    return {r["key"]: r["value"] for r in rows}


@router.patch("/settings")
async def update_settings(body: SettingsPatch, admin: SuperAdmin) -> dict:
    data = body.model_dump(exclude_none=True)
    if not data:
        raise validation("Nothing to update")
    await run(db().table("settings").upsert([{"key": k, "value": v} for k, v in data.items()]))
    return await get_settings(admin)


# ── staff ─────────────────────────────────────────────────────────────────────

@router.get("/staff")
async def list_staff(admin: SuperAdmin) -> dict:
    rows = await run(
        db().table("customers").select("id, telegram_id, full_name, phone, role")
        .neq("role", "customer").order("role")
    )
    return {"staff": rows}


@router.get("/customers")
async def search_customers(
    admin: SuperAdmin,
    q: Optional[str] = Query(default=None, max_length=64, description="name, phone or Telegram ID"),
) -> dict:
    """Find a person to appoint as admin — by name, phone or Telegram ID."""
    query = db().table("customers").select("id, telegram_id, full_name, phone, role")
    term = "".join(ch for ch in (q or "") if ch not in ',()*%:\\"\'').strip()
    if term:
        digits = "".join(ch for ch in term if ch.isdigit())
        conditions = [f"full_name.ilike.*{term}*"]
        if digits:
            conditions.append(f"phone.ilike.*{digits}*")
            if digits == term and len(digits) <= 15:
                conditions.append(f"telegram_id.eq.{digits}")
        query = query.or_(",".join(conditions))
    rows = await run(query.order("created_at", desc=True).limit(20))
    return {"customers": rows}


@router.put("/staff/{telegram_id}")
async def set_staff_role(telegram_id: int, body: StaffRoleRequest, admin: SuperAdmin) -> dict:
    """
    Give or take a role. The person must have opened the shop at least once.
    Super admins come only from SUPER_ADMIN_IDS and can't be changed here.
    """
    person = await first(db().table("customers").select("id, role").eq("telegram_id", telegram_id))
    if person is None:
        raise not_found("This user has not opened the shop yet")
    if person["role"] == "super_admin":
        raise forbidden("Super admin role is managed in server settings")
    rows = await run(db().table("customers").update({"role": body.role}).eq("id", person["id"]))
    r = rows[0]
    return {k: r[k] for k in ("id", "telegram_id", "full_name", "phone", "role")}
