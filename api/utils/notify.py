import logging
from typing import Optional

import httpx

from api.config import BOT_TOKEN, ADMIN_NOTIFY_IDS

logger = logging.getLogger(__name__)

_TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = "HTML",
) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_TG_API}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            )
            return resp.json().get("ok", False)
    except Exception as e:
        logger.error("send_message error: %s", e)
        return False


async def notify_admin_new_order(
    order: dict,
    customer: dict,
    items: list[dict],
) -> None:
    short_id = order["id"][-8:].upper()
    delivery = "🏪 Olib ketish" if order.get("delivery_type") == "pickup" else "🚚 Yetkazib berish"
    lines = [
        f"🛍️ <b>Yangi buyurtma #{short_id}</b>",
        f"👤 {customer.get('full_name', '—')} | {customer.get('phone', '—')}",
        f"📦 {delivery}",
        "",
    ]
    for item in items:
        name = item.get("product_name", item.get("product_id", "?")[-6:])
        qty = item.get("quantity", 0)
        price = float(item.get("unit_price", 0))
        lines.append(f"  • {name} × {qty} = {qty * price:,.0f} so'm")

    total = float(order.get("total_amount", 0))
    lines.append(f"\n💰 <b>Jami: {total:,.0f} so'm</b>")

    if order.get("address"):
        lines.append(f"📍 {order['address']}")
    if order.get("notes"):
        lines.append(f"📝 {order['notes']}")

    for chat_id in ADMIN_NOTIFY_IDS:
        await send_message(chat_id, "\n".join(lines))


async def notify_admin_new_payment(
    payment: dict,
    order: dict,
    customer: dict,
) -> None:
    short_id = order["id"][-8:].upper()
    method_labels = {"card": "💳 Bank kartasi", "click": "📱 Click", "payme": "📱 Payme", "cash": "💵 Naqd"}
    method = method_labels.get(payment.get("method", ""), payment.get("method", "—"))
    amount = float(payment.get("amount", 0))

    text = (
        f"💳 <b>Yangi to'lov</b>\n"
        f"📋 Buyurtma: <b>#{short_id}</b>\n"
        f"👤 {customer.get('full_name', '—')} | {customer.get('phone', '—')}\n"
        f"💰 Summa: <b>{amount:,.0f} so'm</b>\n"
        f"💳 Usul: {method}\n"
    )
    if payment.get("receipt_file_id"):
        text += f"📎 Chek: {payment['receipt_file_id']}"

    for chat_id in ADMIN_NOTIFY_IDS:
        await send_message(chat_id, text)


async def notify_customer_payment_confirmed(
    telegram_id: str,
    order_id: str,
    language: str = "uz",
) -> None:
    short_id = order_id[-8:].upper()
    messages = {
        "uz": f"✅ <b>To'lovingiz tasdiqlandi!</b>\nBuyurtma <b>#{short_id}</b> ishlanmoqda.",
        "ru": f"✅ <b>Ваш платёж подтверждён!</b>\nЗаказ <b>#{short_id}</b> в обработке.",
        "en": f"✅ <b>Payment confirmed!</b>\nOrder <b>#{short_id}</b> is being processed.",
    }
    await send_message(telegram_id, messages.get(language, messages["uz"]))
