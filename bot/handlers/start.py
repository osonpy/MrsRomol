"""
start.py — /start and any other message: greet and offer the Mini App.
The whole shop lives in the Mini App, so the bot has no menus of its own.
"""
from html import escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from bot.config import MINI_APP_URL
from bot.texts import GREETING, OPEN_SHOP, lang_of

router = Router()


def shop_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=OPEN_SHOP[lang], web_app=WebAppInfo(url=MINI_APP_URL))]]
    )


@router.message(CommandStart())
@router.message()
async def greet(message: Message) -> None:
    if message.chat.type != "private":  # stay quiet in the admin group
        return
    user = message.from_user
    lang = lang_of(user.language_code if user else None)
    name = escape(user.first_name) if user and user.first_name else ""
    await message.answer(GREETING[lang].format(name=name), reply_markup=shop_keyboard(lang))
