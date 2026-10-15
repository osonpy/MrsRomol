"""
payments.py — "✅ Tasdiqlash / ❌ Rad etish" buttons under a receipt.

The API sends each new receipt to the admin chats with these buttons
(api/notify.py → admin_new_payment). Approving here does exactly what the
admin section of the Mini App does (api/actions.py), and the message is
updated to show who decided.
"""
import logging
from html import escape
from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from api import actions, notify
from api.errors import AppError

logger = logging.getLogger(__name__)
router = Router()


def _markup(rows: list[list[dict[str, Any]]]) -> InlineKeyboardMarkup | None:
    rows = [r for r in rows if r]
    return InlineKeyboardMarkup.model_validate({"inline_keyboard": rows}) if rows else None


def _details_row(chat_id: int, order: dict[str, Any]) -> list[dict[str, Any]]:
    btn = notify.open_button(chat_id, *notify.order_button("📋 Batafsil", order, admin=True))
    return [btn] if btn else []


async def _admin_of(callback: CallbackQuery) -> dict[str, Any] | None:
    u = callback.from_user
    customer = await actions.ensure_customer(
        {"id": u.id, "first_name": u.first_name, "last_name": u.last_name, "language_code": u.language_code}
    )
    return customer if customer["role"] in actions.ADMIN_ROLES else None


async def _edit(callback: CallbackQuery, text: str | None, markup: InlineKeyboardMarkup | None) -> None:
    msg = callback.message
    try:
        if text is None:
            await msg.edit_reply_markup(reply_markup=markup)
        elif msg.photo:
            await msg.edit_caption(caption=text, reply_markup=markup)
        else:
            await msg.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:  # e.g. "message is not modified"
        logger.info("edit skipped: %s", e)


@router.callback_query(F.data.startswith("pay:"))
async def on_payment_button(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    action, payment_id = parts[1], parts[-1]

    admin = await _admin_of(callback)
    if admin is None:
        await callback.answer("Bu tugmalar faqat adminlar uchun", show_alert=True)
        return

    if action == "no":  # show the reasons
        await _edit(callback, None, _markup(notify.reject_rows(payment_id)))
        await callback.answer("Sababni tanlang")
        return
    if action == "back":
        await _edit(callback, None, _markup(notify.review_rows(payment_id)))
        await callback.answer()
        return

    approve = action == "ok"
    reason = ""
    if action == "r":
        try:
            reason = notify.REJECT_REASONS[int(parts[2])]
        except (IndexError, ValueError):
            await callback.answer("Notoʻgʻri tugma", show_alert=True)
            return

    try:
        order = await actions.review_payment(payment_id, admin, approve, reason)
    except AppError as e:
        if e.code == "ALREADY_REVIEWED":
            await _edit(callback, None, None)
            await callback.answer("Bu chek allaqachon koʻrib chiqilgan", show_alert=True)
        else:
            logger.warning("review_payment %s failed: %s", payment_id, e.code)
            await callback.answer(f"Xatolik: {e.code}", show_alert=True)
        return

    await actions.notify_review(order, approve, reason)
    who = escape(admin["full_name"] or "admin")
    verdict = f"✅ <b>Tasdiqlandi</b> — {who}" if approve else f"❌ <b>Rad etildi</b>: {escape(reason)} — {who}"
    await _edit(callback, f"{callback.message.html_text}\n\n{verdict}", _markup([_details_row(callback.message.chat.id, order)]))
    await callback.answer("Tasdiqlandi ✅" if approve else "Rad etildi")
