"""
notify.py — Telegram messages sent by the API and the bot (Bot API over HTTP).

Admins get new orders and receipts (with approve/reject buttons that the bot
handles); customers get every status change in their language; subscribers
get new-product announcements. Sending never raises: a failed notification
must not break an order.
"""
import asyncio
import logging
from html import escape
from typing import Any

import httpx

from api.config import ADMIN_NOTIFY_IDS, BOT_TOKEN, MINI_APP_LINK, MINI_APP_URL
from api.constants import DELIVERY_METHODS, REGIONS

logger = logging.getLogger(__name__)

_TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Telegram refused because the user blocked the bot or never started it.
BLOCKED = "blocked"


async def tg(method: str, payload: dict[str, Any]) -> Any:
    """Call a Bot API method. Returns the result, None on failure, or BLOCKED."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{_TG_API}/{method}", json=payload)
        data = resp.json()
    except Exception as e:
        logger.error("%s to %s error: %s", method, payload.get("chat_id"), e)
        return None
    if data.get("ok"):
        return data.get("result")
    if data.get("error_code") == 403:
        return BLOCKED
    logger.warning("%s to %s failed: %s", method, payload.get("chat_id"), str(data)[:200])
    return None


def open_button(chat_id: int | str, label: str, path: str, start_param: str) -> dict[str, Any] | None:
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


def _markup(rows: list[list[dict[str, Any] | None]]) -> dict[str, Any] | None:
    rows = [[b for b in row if b] for row in rows]
    rows = [row for row in rows if row]
    return {"inline_keyboard": rows} if rows else None


async def send_message(
    chat_id: int | str,
    text: str,
    button: tuple[str, str, str] | None = None,
    extra_rows: list[list[dict[str, Any]]] | None = None,
) -> Any:
    """button = (label, Mini App path, startapp parameter)."""
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    markup = _markup([*(extra_rows or []), [open_button(chat_id, *button) if button else None]])
    if markup:
        payload["reply_markup"] = markup
    return await tg("sendMessage", payload)


async def send_photo(
    chat_id: int | str,
    photo_url: str,
    caption: str,
    button: tuple[str, str, str] | None = None,
    extra_rows: list[list[dict[str, Any]]] | None = None,
) -> Any:
    payload: dict[str, Any] = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    markup = _markup([*(extra_rows or []), [open_button(chat_id, *button) if button else None]])
    if markup:
        payload["reply_markup"] = markup
    return await tg("sendPhoto", payload)


def money(amount: int | float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def order_button(label: str, order: dict[str, Any], admin: bool = False) -> tuple[str, str, str]:
    if admin:
        return label, f"/admin/orders/{order['id']}", f"admin_order_{order['id']}"
    return label, f"/orders/{order['id']}", f"order_{order['id']}"


# ── admins ────────────────────────────────────────────────────────────────────

_REGION_UZ = {r["code"]: r["uz"] for r in REGIONS}
_METHOD_UZ = {m["code"]: m["uz"] for m in DELIVERY_METHODS}

# Reasons offered by the bot's "Reject" button (index goes in callback data).
REJECT_REASONS = ["Chek o'qilmaydi", "Summa mos emas", "Pul kelib tushmadi", "Boshqa buyurtmaning cheki"]


def review_rows(payment_id: str) -> list[list[dict[str, Any]]]:
    return [[
        {"text": "✅ Tasdiqlash", "callback_data": f"pay:ok:{payment_id}"},
        {"text": "❌ Rad etish", "callback_data": f"pay:no:{payment_id}"},
    ]]


def reject_rows(payment_id: str) -> list[list[dict[str, Any]]]:
    rows = [[{"text": r, "callback_data": f"pay:r:{i}:{payment_id}"}] for i, r in enumerate(REJECT_REASONS)]
    rows.append([{"text": "↩️ Orqaga", "callback_data": f"pay:back:{payment_id}"}])
    return rows


async def admin_new_order(order: dict[str, Any], items: list[dict[str, Any]]) -> None:
    lines = [
        f"🛍 <b>Yangi buyurtma #{order['number']}</b>",
        f"👤 {escape(order['contact_name'])} · {escape(order['contact_phone'])}",
        f"🚚 {_METHOD_UZ.get(order['delivery_method'], order['delivery_method'])}"
        f" · {escape(_REGION_UZ.get(order['region'], order['region']))}",
        "",
    ]
    for it in items:
        variant = " / ".join(escape(v) for v in (it.get("color_uz"), it.get("size")) if v)
        lines.append(
            f"• {escape(it['product_name_uz'])}{f' ({variant})' if variant else ''}"
            f" × {it['quantity']} = {money(it['unit_price'] * it['quantity'])}"
        )
    if order.get("discount"):
        lines.append(f"🎟 Chegirma: −{money(order['discount'])}")
    lines.append(f"\n💰 <b>Jami: {money(order['total'])}</b>")
    lines.append("⏳ To'lov kutilmoqda")
    text = "\n".join(lines)
    for chat_id in ADMIN_NOTIFY_IDS:
        await send_message(chat_id, text, order_button("📋 Ochish", order, admin=True))


def payment_caption(order: dict[str, Any]) -> str:
    return (
        f"💳 <b>Chek keldi — #{order['number']}</b>\n"
        f"👤 {escape(order['contact_name'])} · {escape(order['contact_phone'])}\n"
        f"💰 <b>{money(order['total'])}</b>"
    )


async def admin_new_payment(order: dict[str, Any], payment_id: str, receipt_url: str | None) -> None:
    """Receipt photo + approve/reject buttons, handled by the bot (bot/handlers/payments.py)."""
    caption = payment_caption(order)
    button = order_button("📋 Batafsil", order, admin=True)
    for chat_id in ADMIN_NOTIFY_IDS:
        sent = None
        if receipt_url:
            sent = await send_photo(chat_id, receipt_url, caption, button, review_rows(payment_id))
        if not sent or sent == BLOCKED:  # e.g. HEIC isn't a Telegram photo: text + buttons instead
            await send_message(chat_id, caption + "\n\nChekni «Batafsil» orqali ko'ring.", button, review_rows(payment_id))


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
        total=money(order.get("total", 0)),
        minutes=minutes,
        tracking=f"\n📮 {label}: <code>{escape(order['tracking_number'])}</code>" if order.get("tracking_number") else "",
        reason=f"\n💬 {escape(reason)}" if reason else "",
    )
    await send_message(telegram_id, text, order_button(_BUTTON[lang], order))


# ── new product announcements ────────────────────────────────────────────────

_ANNOUNCE = {
    "uz": ("🌸 <b>Yangi:</b> {name}\n💰 {price}", "👀 Ko'rish"),
    "ru": ("🌸 <b>Новинка:</b> {name}\n💰 {price}", "👀 Смотреть"),
}


async def announce_product(product: dict[str, Any], image_url: str, price: int, subscribers: list[dict[str, Any]]) -> list[str]:
    """
    Send a new product to every subscriber, ~20 messages a second (Telegram's
    limit is 30). Returns ids of customers who blocked the bot.
    """
    blocked: list[str] = []
    for c in subscribers:
        lang = c["language"] if c["language"] in _ANNOUNCE else "uz"
        template, label = _ANNOUNCE[lang]
        name = product[f"name_{lang}"] or product["name_uz"]
        caption = template.format(name=escape(name), price=escape(money(price)))
        button = (label, f"/product/{product['id']}", f"product_{product['id']}")
        if await send_photo(c["telegram_id"], image_url, caption, button) == BLOCKED:
            blocked.append(c["id"])
        await asyncio.sleep(0.05)
    return blocked
