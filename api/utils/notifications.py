"""
api/utils/notifications.py — Send Telegram bot notifications to users and admin.
Uses httpx async client to call Bot API directly (no aiogram dependency).
"""
import logging
from typing import Optional

import httpx

from api.config import BOT_TOKEN, ADMIN_GROUP_ID

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: Optional[dict] = None,
) -> bool:
    """Send a message via Bot API. Returns True on success."""
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        import json
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
            data = resp.json()
            if not data.get("ok"):
                logger.warning("sendMessage failed: %s", data)
                return False
            return True
    except Exception as e:
        logger.error("send_message error: %s", e)
        return False


async def notify_admin_new_order(
    order: dict,
    customer: dict,
    items: list[dict],
) -> None:
    """
    Send new order notification to admin group.
    Includes order details and inline buttons for confirm/cancel.
    """
    order_id = order["id"]
    short_id = order_id[-8:].upper()
    customer_name = customer.get("full_name", "—")
    phone = customer.get("phone", "—")
    total = f"{order['total_amount']:,.0f}".replace(",", " ")
    delivery = "Yetkazib berish" if order["delivery_type"] == "delivery" else "O'zim olaman"

    items_text = "\n".join(
        f"  • {item.get('product_name', item['product_id'])} × {item['quantity']} = "
        f"{item['unit_price'] * item['quantity']:,.0f} so'm"
        for item in items
    )

    notes = order.get("notes", "")
    address_line = ""
    if notes and notes.startswith("address:"):
        lines = notes.split("\n", 1)
        address_line = f"📍 Manzil: {lines[0].replace('address:', '').strip()}\n"
        notes = lines[1].strip() if len(lines) > 1 else ""

    text = (
        f"🛒 <b>YANGI BUYURTMA (Mini App)</b>\n\n"
        f"👤 Mijoz: {customer_name}\n"
        f"📱 Telefon: {phone}\n"
        f"🆔 Buyurtma: <code>{short_id}</code>\n\n"
        f"📦 <b>Mahsulotlar:</b>\n{items_text}\n\n"
        f"💰 Jami: <b>{total} so'm</b>\n"
        f"🚚 Yetkazish: {delivery}\n"
        f"{address_line}"
        f"📅 Sana: {order.get('created_at', '')[:16].replace('T', ' ')}"
    )

    # Admin action keyboard
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Tasdiqlash", "callback_data": f"adm_oc:{order_id}"},
                {"text": "❌ Bekor qilish", "callback_data": f"adm_ox:{order_id}"},
            ]
        ]
    }

    await send_message(ADMIN_GROUP_ID, text, reply_markup=keyboard)


async def notify_admin_new_payment(
    payment: dict,
    order: dict,
    customer: dict,
) -> None:
    """Notify admin about a new payment receipt."""
    order_id = order["id"]
    short_id = order_id[-8:].upper()
    customer_name = customer.get("full_name", "—")
    amount = f"{payment['amount']:,.0f}".replace(",", " ")
    method = payment.get("method", "card")
    receipt_url = payment.get("receipt_url", "")

    text = (
        f"💳 <b>TO'LOV CHEKI KELDI (Mini App)</b>\n\n"
        f"👤 Mijoz: {customer_name}\n"
        f"🆔 Buyurtma: <code>{short_id}</code>\n"
        f"💰 Summa: {amount} so'm\n"
        f"💳 Usul: {method}\n"
        f"📅 Sana: {payment.get('paid_at', '')[:16].replace('T', ' ')}"
    )

    if receipt_url:
        text += f"\n🖼 <a href='{receipt_url}'>Chekni ko'rish</a>"

    payment_id = payment["id"]
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ To'lovni tasdiqlash", "callback_data": f"adm_pv:{order_id}"},
                {"text": "❌ Rad etish", "callback_data": f"adm_pr:{order_id}"},
            ]
        ]
    }

    await send_message(ADMIN_GROUP_ID, text, reply_markup=keyboard)


async def notify_customer_payment_confirmed(
    telegram_id: str,
    order_id: str,
    language: str = "uz",
) -> None:
    """Notify customer that their payment was confirmed."""
    short_id = order_id[-8:].upper()
    messages = {
        "uz": (
            f"💚 <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"🆔 Buyurtma: <code>{short_id}</code>\n"
            f"📊 Holat: 🚚 Tayyorlanmoqda\n\n"
            f"Tez orada yetkazib beramiz!"
        ),
        "ru": (
            f"💚 <b>Ваш платёж подтверждён!</b>\n\n"
            f"🆔 Заказ: <code>{short_id}</code>\n"
            f"📊 Статус: 🚚 Готовится\n\n"
            f"Доставим в ближайшее время!"
        ),
        "en": (
            f"💚 <b>Payment confirmed!</b>\n\n"
            f"🆔 Order: <code>{short_id}</code>\n"
            f"📊 Status: 🚚 Being prepared\n\n"
            f"We'll deliver soon!"
        ),
    }
    text = messages.get(language, messages["uz"])
    await send_message(int(telegram_id), text)
