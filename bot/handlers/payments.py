"""
handlers/payments.py
Handles the receipt photo upload step that follows order confirmation.

The user's order_id and total_amount are still in FSM storage
(set by orders.py cb_confirm_order and cleared only after receipt is saved).
"""
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import ADMIN_GROUP_ID
from bot.database import get_customer, create_payment, get_order_by_id
from bot.keyboards.admin import admin_payment_keyboard
from bot.messages import get_message
from bot.utils.formatters import format_price

logger = logging.getLogger(__name__)
router = Router()


async def _get_lang(telegram_id: str) -> str:
    customer = await get_customer(str(telegram_id))
    return customer.get("language", "uz") if customer else "uz"


# ── Receipt photo handler ──────────────────────────────────────────────────────

@router.message(F.photo)
async def msg_receipt_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Triggered whenever a user sends a photo.
    We check FSM data to see if there's a pending order awaiting payment proof.
    If not, the photo is silently ignored (no active order flow).
    """
    lang = await _get_lang(message.from_user.id)
    data = await state.get_data()
    order_id = data.get("order_id")

    if not order_id:
        # No active order — photo not expected in this context; ignore silently
        return

    # Use the highest-resolution version of the photo
    photo = message.photo[-1]
    file_id = photo.file_id

    # Retrieve order to get total_amount for the payment record
    order = await get_order_by_id(order_id)
    amount = order.get("total_amount", 0) if order else data.get("total_amount", 0)

    # Save payment record — receipt_url stores the Telegram file_id
    payment = await create_payment(
        order_id=order_id,
        amount=float(amount),
        receipt_url=file_id,   # file_id acts as the receipt reference
        method="card",
        status="pending_verification",
    )

    if not payment:
        await message.answer(get_message("receipt_error", lang))
        return

    # ── Confirm to user ────────────────────────────────────────────────────────
    await message.answer(
        get_message("receipt_received", lang, order_id=order_id),
        parse_mode="HTML",
    )

    # ── Notify admin group — forward the photo + caption ─────────────────────
    customer = await get_customer(str(message.from_user.id))
    customer_name = customer.get("full_name", "—") if customer else "—"

    admin_caption = get_message(
        "admin_new_payment",
        "ru",  # Admin messages in Russian
        customer_name=customer_name,
        order_id=order_id,
        amount=format_price(amount),
        date=datetime.now().strftime("%d.%m.%Y %H:%M"),
    )

    try:
        await bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=file_id,
            caption=admin_caption,
            parse_mode="HTML",
            reply_markup=admin_payment_keyboard(order_id),  # ✅/❌ verify buttons
        )
    except Exception as e:
        logger.error("Admin payment notification failed: %s", e)

    # Clear only the payment-related FSM keys; do not wipe the entire state
    await state.update_data(order_id=None, total_amount=None)
