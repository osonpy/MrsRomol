"""
notify.py — Telegram messages sent by the API (via Bot API over HTTP, no aiogram).

Admins get new orders / new receipts; customers get every status change in
their language. All functions swallow errors: a failed notification must
never break an order.
"""
import logging
from html import escape
from typing import Any

import httpx

from api.config import ADMIN_NOTIFY_IDS, BOT_TOKEN, MINI_APP_LINK, MINI_APP_URL

logger = logging.getLogger(__name__)

_TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _open_button(chat_id: int | str, label: str, path: str, start_param: str) -> dict[str, Any] | None:
    """
    Button that opens the Mini App on `path`. Telegram allows web_app buttons
    only in private chats; in groups we use the Mini App direct link
    (t.me/<bot>/<app>?startapp=...) when MINI_APP_LINK is configured.
    """
    if int(chat_id) > 0:
        return {"text": label, "web_app": {"url": f"{MINI_APP_URL}{path}"}}
    if MINI_APP_LINK:
        return {"text": label, "url": f"{MINI_APP_LINK}?startapp={start_param}"}
    return None


async def send_message(
    chat_id: int | str, text: str, button: tuple[str, str, str] | None = None
) -> bool:
    """button = (label, Mini App path, startapp parameter)."""
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    btn = _open_button(chat_id, *button) if button else None
    if btn:
        payload["reply_markup"] = {"inline_keyboard": [[btn]]}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{_TG_API}/sendMessage", json=payload)
            ok = resp.json().get("ok", False)
            if not ok:
                logger.warning("sendMessage to %s failed: %s", chat_id, resp.text[:200])
            return ok
    except Exception as e:
        logger.error("sendMessage to %s error: %s", chat_id, e)
        return False


def _money(amount: int | float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def _order_button(label: str, order: dict[str, Any], admin: bool = False) -> tuple[str, str, str]:
    if admin:
        return label, f"/admin/orders/{order['id']}", f"admin_order_{order['id']}"
    return label, f"/orders/{order['id']}", f"order_{order['id']}"


# ── admins ────────────────────────────────────────────────────────────────────

async def admin_new_order(order: dict[str, Any], items: list[dict[str, Any]]) -> None:
    lines = [
        f"🛍 <b>Yangi buyurtma #{order['number']}</b>",
        f"👤 {escape(order['contact_name'])} · {escape(order['contact_phone'])}",
        f"🚚 {escape(order['delivery_method'])} · {escape(order['region'])}",
        "",
    ]
    for it in items:
        variant = " / ".join(escape(v) for v in (it.get("color_uz"), it.get("size")) if v)
        lines.append(
            f"• {escape(it['product_name_uz'])}{f' ({variant})' if variant else ''}"
            f" × {it['quantity']} = {_money(it['unit_price'] * it['quantity'])}"
        )
    if order.get("discount"):
        lines.append(f"🎟 Chegirma: −{_money(order['discount'])}")
    lines.append(f"\n💰 <b>Jami: {_money(order['total'])}</b>")
    lines.append("⏳ To'lov kutilmoqda")
    text = "\n".join(lines)
    for chat_id in ADMIN_NOTIFY_IDS:
        await send_message(chat_id, text, _order_button("📋 Ochish", order, admin=True))


async def admin_new_payment(order: dict[str, Any]) -> None:
    text = (
        f"💳 <b>Chek keldi — #{order['number']}</b>\n"
        f"👤 {escape(order['contact_name'])} · {escape(order['contact_phone'])}\n"
        f"💰 {_money(order['total'])}\n\n"
        f"Tekshirib, tasdiqlang yoki rad eting."
    )
    for chat_id in ADMIN_NOTIFY_IDS:
        await send_message(chat_id, text, _order_button("🔍 Tekshirish", order, admin=True))


# ── customers ─────────────────────────────────────────────────────────────────

_CUSTOMER_TEXT: dict[str, dict[str, str]] = {
    "awaiting_payment": {
        "uz": "🛍 Buyurtma <b>#{n}</b> qabul qilindi.\n💰 {total}\n⏳ To'lovni {minutes} daqiqa ichida qiling va chekni yuboring.",
        "ru": "🛍 Заказ <b>#{n}</b> принят.\n💰 {total}\n⏳ Оплатите в течение {minutes} минут и отправьте чек.",
    },
    "payment_review": {
        "uz": "🔍 Buyurtma <b>#{n}</b>: chek qabul qilindi, tekshirilmoqda.",
        "ru": "🔍 Заказ <b>#{n}</b>: чек получен, проверяем.",
    },
    "confirmed": {
        "uz": "✅ Buyurtma <b>#{n}</b>: to'lov tasdiqlandi! Tez orada yuboramiz.",
        "ru": "✅ Заказ <b>#{n}</b>: оплата подтверждена! Скоро отправим.",
    },
    "shipped": {
        "uz": "🚚 Buyurtma <b>#{n}</b> yuborildi.{tracking}",
        "ru": "🚚 Заказ <b>#{n}</b> отправлен.{tracking}",
    },
    "delivered": {
        "uz": "📦 Buyurtma <b>#{n}</b> yetkazildi. Xaridingiz uchun rahmat! 🌸",
        "ru": "📦 Заказ <b>#{n}</b> доставлен. Спасибо за покупку! 🌸",
    },
    "expired": {
        "uz": "⌛ Buyurtma <b>#{n}</b> bekor qilindi: to'lov vaqti tugadi. Xohlasangiz, qaytadan buyurtma bering.",
        "ru": "⌛ Заказ <b>#{n}</b> отменён: время оплаты истекло. Можете оформить заказ заново.",
    },
    "payment_rejected": {
        "uz": "❌ Buyurtma <b>#{n}</b>: to'lov tasdiqlanmadi.{reason}",
        "ru": "❌ Заказ <b>#{n}</b>: оплата не подтверждена.{reason}",
    },
    "by_admin": {
        "uz": "❌ Buyurtma <b>#{n}</b> do'kon tomonidan bekor qilindi.{reason}",
        "ru": "❌ Заказ <b>#{n}</b> отменён магазином.{reason}",
    },
}
_BUTTON = {"uz": "📦 Buyurtmani ko'rish", "ru": "📦 Открыть заказ"}


async def customer_order_update(
    telegram_id: int,
    language: str,
    order: dict[str, Any],
    event: str,
    reason: str = "",
    minutes: int = 30,
) -> None:
    """event: an order status, or a cancel reason (expired / payment_rejected / by_admin)."""
    lang = language if language in ("uz", "ru") else "uz"
    template = _CUSTOMER_TEXT.get(event, {}).get(lang)
    if not template:
        return
    label = {"uz": "Trek raqami", "ru": "Трек-номер"}[lang]
    text = template.format(
        n=order["number"],
        total=_money(order.get("total", 0)),
        minutes=minutes,
        tracking=f"\n📮 {label}: <code>{escape(order['tracking_number'])}</code>" if order.get("tracking_number") else "",
        reason=f"\n💬 {escape(reason)}" if reason else "",
    )
    await send_message(telegram_id, text, _order_button(_BUTTON[lang], order))
