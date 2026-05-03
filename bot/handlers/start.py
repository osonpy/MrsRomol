import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

from bot.config import MINI_APP_URL

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name or "User"
    lang = message.from_user.language_code or "uz"

    greetings = {
        "uz": f"Assalomu alaykum, {name}! 👋\n\nMisr Romol do'koniga xush kelibsiz. 🧣\nQuyidagi tugma orqali do'konni oching:",
        "ru": f"Привет, {name}! 👋\n\nДобро пожаловать в магазин Misr Romol. 🧣\nОткройте магазин по кнопке ниже:",
        "en": f"Hello, {name}! 👋\n\nWelcome to Misr Romol store. 🧣\nOpen the shop using the button below:",
    }
    text = greetings.get(lang[:2], greetings["uz"])

    btn_labels = {
        "uz": "🛍️ Do'konni ochish",
        "ru": "🛍️ Открыть магазин",
        "en": "🛍️ Open shop",
    }
    btn_text = btn_labels.get(lang[:2], btn_labels["uz"])

    markup = None
    if MINI_APP_URL:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text=btn_text,
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ]]
        )

    await message.answer(text, reply_markup=markup)
