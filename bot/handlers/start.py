"""
handlers/start.py
Handles: /start command, language selection, phone number sharing, /settings.

New user flow:
  /start → Language picker → Phone number request → Welcome + main menu

Returning user flow:
  /start → Welcome back + main menu (no phone re-request if already saved)
"""
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.config import DEFAULT_LANGUAGE
from bot.database import get_customer, upsert_customer, update_customer_language
from bot.keyboards.main_menu import main_menu_keyboard, language_selection_keyboard
from bot.messages import get_message

logger = logging.getLogger(__name__)
router = Router()


# ── FSM: phone number collection for new users ─────────────────────────────────

class RegistrationFSM(StatesGroup):
    waiting_phone = State()


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Entry point for every user.
    - New users:      show language picker.
    - Returning users (with phone): show welcome_back + main menu.
    - Returning users (without phone): ask for phone number.
    """
    telegram_id = str(message.from_user.id)
    full_name = message.from_user.full_name or "User"

    customer = await get_customer(telegram_id)

    if customer:
        lang = customer.get("language", DEFAULT_LANGUAGE)
        # If returning user hasn't shared phone yet — ask again
        if not customer.get("phone"):
            await state.update_data(lang=lang)
            await state.set_state(RegistrationFSM.waiting_phone)
            await message.answer(
                get_message("ask_phone", lang, name=full_name),
                reply_markup=_phone_keyboard(lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                get_message("welcome_back", lang, name=full_name),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="HTML",
            )
    else:
        # Brand-new user — ask for language first
        await message.answer(
            get_message("choose_language", DEFAULT_LANGUAGE),
            reply_markup=language_selection_keyboard(),
        )


# ── Language selection (new users and language changes) ────────────────────────

@router.callback_query(F.data.startswith("lang:"))
async def cb_language_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Unified handler for language selection.
    - New users: creates customer record, then asks for phone.
    - Existing users: updates language field, goes to main menu.
    """
    lang = callback.data.split(":")[1]       # 'uz' | 'ru' | 'en'
    telegram_id = str(callback.from_user.id)
    full_name = callback.from_user.full_name or "User"

    try:
        await callback.message.delete()
    except Exception:
        pass

    existing = await get_customer(telegram_id)

    if existing:
        # Returning user — language change only
        ok = await update_customer_language(telegram_id, lang)
        if not ok:
            await callback.message.answer(get_message("db_error", lang))
            await callback.answer()
            return
        await callback.message.answer(
            get_message("language_changed", lang),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML",
        )
        await callback.answer()
    else:
        # New user — create record with empty phone, then ask for phone
        customer = await upsert_customer(telegram_id, full_name, lang)
        if not customer:
            await callback.message.answer(get_message("db_error", lang))
            await callback.answer()
            return

        # Ask for phone number before showing main menu
        await state.update_data(lang=lang)
        await state.set_state(RegistrationFSM.waiting_phone)
        await callback.message.answer(
            get_message("ask_phone", lang, name=full_name),
            reply_markup=_phone_keyboard(lang),
            parse_mode="HTML",
        )
        await callback.answer()


# ── Phone number handler ────────────────────────────────────────────────────────

@router.message(RegistrationFSM.waiting_phone, F.contact)
async def msg_phone_received(message: Message, state: FSMContext) -> None:
    """User tapped 'Share phone number' button — save to DB and show main menu."""
    from bot.database import update_customer_phone

    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANGUAGE)
    telegram_id = str(message.from_user.id)
    full_name = message.from_user.full_name or "User"
    phone = message.contact.phone_number

    # Normalize: ensure +998... format
    if not phone.startswith("+"):
        phone = "+" + phone

    await update_customer_phone(telegram_id, phone)
    await state.clear()

    await message.answer(
        get_message("welcome", lang, name=full_name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.message(RegistrationFSM.waiting_phone, ~F.contact)
async def msg_phone_skip_or_wrong(message: Message, state: FSMContext) -> None:
    """
    User sent text instead of using the contact button.
    Nudge them to use the button or allow manual entry.
    """
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANGUAGE)

    # Accept manual phone number if it looks valid
    text = (message.text or "").strip()
    digits = text.replace("+", "").replace(" ", "").replace("-", "")
    if digits.isdigit() and 9 <= len(digits) <= 13:
        from bot.database import update_customer_phone
        full_name = message.from_user.full_name or "User"
        phone = text if text.startswith("+") else "+" + digits
        await update_customer_phone(str(message.from_user.id), phone)
        await state.clear()
        await message.answer(
            get_message("welcome", lang, name=full_name),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="HTML",
        )
    else:
        # Not a valid number — ask again
        await message.answer(
            get_message("ask_phone_retry", lang),
            reply_markup=_phone_keyboard(lang),
            parse_mode="HTML",
        )


# ── /settings — open language picker ──────────────────────────────────────────

@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(
        get_message("choose_language", DEFAULT_LANGUAGE),
        reply_markup=language_selection_keyboard(),
    )


# ── Reply-keyboard "Language" button ──────────────────────────────────────────

@router.message(F.text.func(lambda t: t and any(
    t == get_message("btn_language", lc) for lc in ["uz", "ru", "en"]
)))
async def msg_language_button(message: Message) -> None:
    await message.answer(
        get_message("choose_language", DEFAULT_LANGUAGE),
        reply_markup=language_selection_keyboard(),
    )


# ── Internal helper: phone request keyboard ────────────────────────────────────

def _phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """One-time reply keyboard with a 'Share phone' button."""
    share_label = {
        "uz": "📱 Telefon raqamni ulashish",
        "ru": "📱 Поделиться номером",
        "en": "📱 Share phone number",
    }.get(lang, "📱 Telefon raqamni ulashish")

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=share_label, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
