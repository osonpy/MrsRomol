"""
handlers/my_orders.py
Shows the last 10 orders for the current user with localized status badges.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message

from bot.database import get_customer, get_customer_orders
from bot.messages import get_message
from bot.utils.formatters import format_price, format_date, short_uuid

logger = logging.getLogger(__name__)
router = Router()

# Status → message key mapping
STATUS_KEY_MAP = {
    "pending":   "status_pending",
    "confirmed": "status_confirmed",
    "shipped":   "status_shipped",
    "delivered": "status_delivered",
    "cancelled": "status_cancelled",
}


async def _get_customer_and_lang(telegram_id: str) -> tuple[dict | None, str]:
    customer = await get_customer(str(telegram_id))
    lang = customer.get("language", "uz") if customer else "uz"
    return customer, lang


# ── My Orders entry — triggered from reply keyboard ────────────────────────────

@router.message(F.text.func(lambda t: t and any(
    t == get_message("btn_my_orders", lc) for lc in ["uz", "ru", "en"]
)))
async def msg_my_orders(message: Message) -> None:
    """Fetch and display last 10 orders for the user."""
    customer, lang = await _get_customer_and_lang(message.from_user.id)

    if not customer:
        await message.answer(get_message("error_generic", lang))
        return

    orders = await get_customer_orders(customer["id"], limit=10)

    if not orders:
        await message.answer(get_message("no_orders", lang))
        return

    # Build a message per order, joined into one send
    lines = [get_message("my_orders_header", lang)]
    for order in orders:
        status_raw = order.get("status", "pending")
        status_key = STATUS_KEY_MAP.get(status_raw, "status_pending")
        status_label = get_message(status_key, lang)

        lines.append(
            get_message(
                "order_item",
                lang,
                order_id=short_uuid(order["id"]),
                date=format_date(order.get("created_at", "")),
                total=format_price(order.get("total_amount", 0)),
                status=status_label,
            )
        )

    await message.answer("\n\n".join(lines), parse_mode="HTML")


# ── Contact Us — placed here to keep handlers/ self-contained ─────────────────

@router.message(F.text.func(lambda t: t and any(
    t == get_message("btn_contact", lc) for lc in ["uz", "ru", "en"]
)))
async def msg_contact(message: Message) -> None:
    """Show contact info: phone, Instagram, Telegram handle."""
    customer, lang = await _get_customer_and_lang(message.from_user.id)
    await message.answer(
        get_message("contact_info", lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
