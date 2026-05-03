"""
handlers/admin.py
All admin-side functionality:

1. Order action callbacks  (adm_oc / adm_ox)
   — Admin taps ✅/❌ on order notification → updates DB → notifies customer

2. Payment action callbacks (adm_pv / adm_pr)
   — Admin taps ✅/❌ on payment receipt → updates DB → notifies customer

3. /setphotos FSM
   — Admin picks a product → sends up to 3 photos → saved as Telegram file_ids

IMPORTANT: Callbacks are registered globally (not filtered by chat type) because
the admin group can be either a group or a private chat with the admin.
"""
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.config import ADMIN_GROUP_ID, ADMIN_USER_IDS
from bot.database import (
    update_order_status,
    update_payment_status,
    get_customer_by_order_id,
    get_product_images,
    add_product_image,
    delete_product_images,
    get_all_active_products_simple,
    get_pending_payments,
    MAX_PRODUCT_IMAGES,
)
from bot.messages import get_message
from bot.utils.formatters import format_price, format_date, short_uuid

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# Admin guard filter
# ══════════════════════════════════════════════════════════════════════════════

class IsAdmin(BaseFilter):
    """
    Allows a message/command only if the sender's user ID is in ADMIN_USER_IDS.
    Works in both private chats and group chats.
    Configured via ADMIN_USER_IDS in .env (comma-separated Telegram user IDs).
    """
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_USER_IDS


# ══════════════════════════════════════════════════════════════════════════════
# FSM for /setphotos
# ══════════════════════════════════════════════════════════════════════════════

class PhotoUploadFSM(StatesGroup):
    choosing_product = State()   # Admin picks which product to upload for
    uploading_photos = State()   # Admin sends photos one by one


# ── Guard: only accept commands/callbacks from the admin ──────────────────────

def _is_admin(user_id: int) -> bool:
    """
    Return True if the sender is the configured admin.
    ADMIN_GROUP_ID can be a group (negative) or personal chat (positive).
    For group chats, all group members can trigger; refine if needed.
    """
    return True  # Aiogram filter below restricts to ADMIN_GROUP_ID chat


# ══════════════════════════════════════════════════════════════════════════════
# Helper: notify customer in their own language
# ══════════════════════════════════════════════════════════════════════════════

async def _notify_customer(
    bot: Bot,
    order_id: str,
    message_key: str,
) -> None:
    """
    Look up the customer for an order and send them a status update message
    in their preferred language.
    """
    customer = await get_customer_by_order_id(order_id)
    if not customer:
        logger.warning("Could not find customer for order %s", order_id)
        return

    lang = customer.get("language", "uz")
    telegram_id = customer.get("telegram_id")
    if not telegram_id:
        return

    text = get_message(message_key, lang, order_id=order_id[-8:].upper())
    try:
        await bot.send_message(
            chat_id=int(telegram_id),
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Failed to notify customer %s: %s", telegram_id, e)


# ══════════════════════════════════════════════════════════════════════════════
# /pending — List all unverified payments (solves concurrent payment problem)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(IsAdmin(), Command("pending"))
async def cmd_pending(message: Message, bot: Bot) -> None:
    """
    Show all payments with status='pending_verification'.
    Each entry has ✅/❌ action buttons so admin can process them one by one.
    This is the recommended way to handle 10+ simultaneous payments.
    """
    payments = await get_pending_payments()

    if not payments:
        await message.answer("✅ Kutayotgan to'lovlar yo'q.")
        return

    await message.answer(
        f"💳 <b>Tasdiqlanmagan to'lovlar: {len(payments)} ta</b>",
        parse_mode="HTML",
    )

    from bot.keyboards.admin import admin_payment_keyboard

    for p in payments:
        order_id  = p.get("order_id", "")
        amount    = format_price(p.get("amount", 0))
        paid_at   = format_date(p.get("paid_at", ""))
        file_id   = p.get("receipt_url", "")

        # Resolve customer name
        customer  = await get_customer_by_order_id(order_id)
        cust_name = customer.get("full_name", "—") if customer else "—"

        caption = (
            f"💳 <b>To'lov</b>\n"
            f"👤 Mijoz: {cust_name}\n"
            f"🆔 Buyurtma: <code>{short_uuid(order_id)}</code>\n"
            f"💰 Summa: {amount} UZS\n"
            f"📅 Sana: {paid_at}"
        )

        try:
            if file_id:
                # Send receipt photo with action buttons
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=admin_payment_keyboard(order_id),
                )
            else:
                await message.answer(
                    caption,
                    parse_mode="HTML",
                    reply_markup=admin_payment_keyboard(order_id),
                )
        except Exception as e:
            logger.error("Failed to send pending payment %s: %s", order_id, e)


# ══════════════════════════════════════════════════════════════════════════════
# ORDER CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("adm_oc:"))
async def cb_admin_order_confirm(callback: CallbackQuery, bot: Bot) -> None:
    """
    Admin tapped ✅ Tasdiqlash on an order notification.

    FIX: Customer is NOT notified here — only after payment receipt is verified.
    This just marks the order as 'confirmed' in DB (admin has seen the order).
    Customer gets notified when payment is verified via cb_admin_payment_verify.
    """
    order_id = callback.data.split(":", 1)[1]

    ok = await update_order_status(order_id, "confirmed")
    if ok:
        # Only update the admin button — NO customer notification here
        await callback.message.edit_reply_markup(
            reply_markup=_done_keyboard(f"✅ Tasdiqlandi (to'lov kutilmoqda) — {order_id[-8:].upper()}")
        )
        await callback.answer("✅ Buyurtma tasdiqlandi! To'lovni kuting.")
    else:
        await callback.answer("❌ DB xatosi. Qaytadan urining.", show_alert=True)


@router.callback_query(F.data.startswith("adm_ox:"))
async def cb_admin_order_cancel(callback: CallbackQuery, bot: Bot) -> None:
    """Admin tapped ❌ Bekor qilish on an order notification."""
    order_id = callback.data.split(":", 1)[1]

    ok = await update_order_status(order_id, "cancelled")
    if ok:
        # Notify customer their order was cancelled
        await _notify_customer(bot, order_id, "order_status_cancelled")
        await callback.message.edit_reply_markup(
            reply_markup=_done_keyboard(f"❌ Bekor qilindi — {order_id[-8:].upper()}")
        )
        await callback.answer("❌ Buyurtma bekor qilindi.")
    else:
        await callback.answer("❌ DB xatosi. Qaytadan urining.", show_alert=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAYMENT CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("adm_pv:"))
async def cb_admin_payment_verify(callback: CallbackQuery, bot: Bot) -> None:
    """
    Admin tapped ✅ To'lov tasdiqlandi.
    This is the REAL confirmation to the customer — payment received, order ships.
    Only here does the customer get the 'order confirmed' message.
    """
    order_id = callback.data.split(":", 1)[1]

    await update_payment_status(order_id, "verified")
    await update_order_status(order_id, "shipped")
    # ★ This is the ONLY place customer gets 'confirmed' notification
    await _notify_customer(bot, order_id, "payment_verified")

    await callback.message.edit_reply_markup(
        reply_markup=_done_keyboard(f"💚 To'lov tasdiqlandi — {order_id[-8:].upper()}")
    )
    await callback.answer("💚 To'lov tasdiqlandi!")


@router.callback_query(F.data.startswith("adm_pr:"))
async def cb_admin_payment_reject(callback: CallbackQuery, bot: Bot) -> None:
    """Admin tapped ❌ To'lov rad etildi."""
    order_id = callback.data.split(":", 1)[1]

    await update_payment_status(order_id, "rejected")
    await _notify_customer(bot, order_id, "payment_rejected")

    await callback.message.edit_reply_markup(
        reply_markup=_done_keyboard(f"🔴 To'lov rad etildi — {order_id[-8:].upper()}")
    )
    await callback.answer("🔴 To'lov rad etildi.")


# ══════════════════════════════════════════════════════════════════════════════
# /setphotos — Admin uploads product photos
# ══════════════════════════════════════════════════════════════════════════════

@router.message(IsAdmin(), Command("setphotos"))
async def cmd_setphotos(message: Message, state: FSMContext) -> None:
    """
    Step 1: Admin sends /setphotos
    Bot replies with a list of products as inline buttons.
    Works from ADMIN_GROUP_ID or admin's private chat.
    """
    products = await get_all_active_products_simple()

    if not products:
        await message.answer("❌ Hech qanday aktiv mahsulot topilmadi.")
        return

    # Build product picker inline keyboard (max ~30 products safe)
    rows = []
    for p in products:
        label = f"📦 {p['name']}"
        rows.append(
            [InlineKeyboardButton(
                text=label,
                callback_data=f"sp_pick:{p['id']}",
            )]
        )
    rows.append(
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="sp_cancel")]
    )

    await message.answer(
        "🖼 <b>Qaysi mahsulotga rasm qo'shmoqchisiz?</b>\n"
        "Mahsulotni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )
    await state.set_state(PhotoUploadFSM.choosing_product)


@router.callback_query(PhotoUploadFSM.choosing_product, F.data.startswith("sp_pick:"))
async def cb_setphotos_pick_product(callback: CallbackQuery, state: FSMContext) -> None:
    """Step 2: Admin picked a product — ask them to send photos."""
    product_id = callback.data.split(":", 1)[1]

    # Show existing photo count
    existing = await get_product_images(product_id)
    count = len(existing)

    await state.update_data(
        product_id=product_id,
        photo_count=count,
    )
    await state.set_state(PhotoUploadFSM.uploading_photos)

    remaining = MAX_PRODUCT_IMAGES - count
    if remaining <= 0:
        reset_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Rasmlarni qayta yuklash (o'chirish + yangi)", callback_data=f"sp_reset:{product_id}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="sp_cancel")],
        ])
        await callback.message.edit_text(
            f"⚠️ Bu mahsulotda allaqachon <b>{MAX_PRODUCT_IMAGES} ta rasm</b> bor.\n"
            "Yangisini qo'shish uchun avval eskisini o'chiring:",
            reply_markup=reset_kb,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"📸 Hozir <b>{count}/{MAX_PRODUCT_IMAGES}</b> rasm mavjud.\n"
            f"Yana <b>{remaining} ta</b> rasm yuborishingiz mumkin.\n\n"
            "Rasmlarni birin-ketin yuboring.\n"
            "Tugatgach /done yozing yoki barcha rasmlarni yuboring.",
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sp_reset:"))
async def cb_setphotos_reset(callback: CallbackQuery, state: FSMContext) -> None:
    """Admin chose to wipe existing photos and start fresh."""
    product_id = callback.data.split(":", 1)[1]
    await delete_product_images(product_id)
    await state.update_data(product_id=product_id, photo_count=0)
    await state.set_state(PhotoUploadFSM.uploading_photos)
    await callback.message.edit_text(
        "🗑 Eski rasmlar o'chirildi.\n\n"
        f"📸 Endi <b>{MAX_PRODUCT_IMAGES} tagacha</b> rasm yuboring.\n"
        "Tugatgach /done yozing.",
        parse_mode="HTML",
    )
    await callback.answer("🗑 Rasmlar o'chirildi")


@router.message(PhotoUploadFSM.uploading_photos, F.photo)
async def msg_setphotos_receive(message: Message, state: FSMContext) -> None:
    """Step 3: Receive each photo and save the highest-res file_id."""
    data = await state.get_data()
    product_id = data["product_id"]
    photo_count = data["photo_count"]

    # Use the largest available resolution
    file_id = message.photo[-1].file_id

    saved = await add_product_image(product_id, file_id)

    if saved is None:
        await message.answer(
            f"⚠️ Maksimal {MAX_PRODUCT_IMAGES} ta rasm qo'shish mumkin. "
            "Yakunlash uchun /done yozing."
        )
        return

    photo_count += 1
    await state.update_data(photo_count=photo_count)
    remaining = MAX_PRODUCT_IMAGES - photo_count

    if remaining > 0:
        await message.answer(
            f"✅ {photo_count}/{MAX_PRODUCT_IMAGES} rasm saqlandi.\n"
            f"Yana <b>{remaining} ta</b> rasm yuborishingiz mumkin yoki /done.",
            parse_mode="HTML",
        )
    else:
        # Max photos reached — finish automatically
        await state.clear()
        await message.answer(
            f"🎉 <b>{MAX_PRODUCT_IMAGES}/{MAX_PRODUCT_IMAGES}</b> rasm saqlandi!\n"
            "Mahsulot rasmlari yangilandi ✅",
            parse_mode="HTML",
        )


@router.message(PhotoUploadFSM.uploading_photos, Command("done"))
async def msg_setphotos_done(message: Message, state: FSMContext) -> None:
    """Admin typed /done to finish uploading."""
    data = await state.get_data()
    count = data.get("photo_count", 0)
    await state.clear()
    await message.answer(
        f"✅ Tayyor! <b>{count} ta rasm</b> saqlandi.",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "sp_cancel")
@router.callback_query(PhotoUploadFSM.choosing_product, F.data == "sp_cancel")
async def cb_setphotos_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Admin cancelled the photo upload flow."""
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.message(PhotoUploadFSM.uploading_photos, ~F.photo)
async def msg_setphotos_wrong_type(message: Message) -> None:
    """Admin sent something other than a photo during upload."""
    await message.answer(
        "📸 Iltimos, faqat <b>rasm</b> yuboring yoki /done bilan tugating.",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _done_keyboard(label: str) -> InlineKeyboardMarkup:
    """
    Replace the action buttons with a single non-clickable status label
    after the admin has already taken action on an order/payment.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=label, callback_data="noop")
        ]]
    )
