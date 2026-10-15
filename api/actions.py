"""
actions.py — operations shared by the API routers and the bot, so a payment
approved from a Telegram button behaves exactly like one approved in the app.
"""
from typing import Any

from api import notify
from api.config import SUPER_ADMIN_IDS
from api.db import db, first, rpc, run
from api.orders import load_order

ADMIN_ROLES = ("admin", "super_admin")


async def ensure_customer(tg_user: dict[str, Any]) -> dict[str, Any]:
    """Load the customer for a Telegram user, creating them on first contact."""
    telegram_id = int(tg_user["id"])
    customer = await first(db().table("customers").select("*").eq("telegram_id", telegram_id))

    if customer is None:
        name = " ".join(p for p in (tg_user.get("first_name"), tg_user.get("last_name")) if p)
        language = "ru" if str(tg_user.get("language_code", "")).startswith("ru") else "uz"
        rows = await run(
            db().table("customers").upsert(
                {
                    "telegram_id": telegram_id,
                    "full_name": name[:128],
                    "language": language,
                    "role": "super_admin" if telegram_id in SUPER_ADMIN_IDS else "customer",
                },
                on_conflict="telegram_id",
            )
        )
        customer = rows[0]
    elif telegram_id in SUPER_ADMIN_IDS and customer["role"] != "super_admin":
        rows = await run(db().table("customers").update({"role": "super_admin"}).eq("id", customer["id"]))
        customer = rows[0]
    return customer


async def review_payment(payment_id: str, admin: dict[str, Any], approve: bool, reason: str = "") -> dict[str, Any]:
    """Approve or reject a receipt; returns the order as loaded for admins."""
    result = await rpc("review_payment", {
        "p_payment_id": payment_id,
        "p_admin_id": admin["id"],
        "p_approve": approve,
        "p_reason": reason or None,
    })
    return await load_order(result["id"], admin=True)


async def notify_review(order: dict[str, Any], approve: bool, reason: str = "") -> None:
    c = order["customer"]
    await notify.customer_order_update(
        c["telegram_id"], c["language"], order, "confirmed" if approve else "payment_rejected", reason,
    )
