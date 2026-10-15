"""
start.py — /start and any other message: greet and offer the Mini App.
The whole shop lives in the Mini App, so the bot has no menus of its own.
"""
from html import escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove, WebAppInfo

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
    await drop_old_keyboard(message)
    await message.answer(GREETING[lang].format(name=name), reply_markup=shop_keyboard(lang))


async def drop_old_keyboard(message: Message) -> None:
    """
    The old bot left a reply keyboard (Katalog / Buyurtmalarim / Bog'lanish / Til)
    under the input field; Telegram keeps it until a bot removes it. A message
    can't carry both that removal and our inline button, so send a throwaway
    message that removes the keyboard and delete it at once.
    """
    try:
        sent = await message.answer("🌸", reply_markup=ReplyKeyboardRemove())
        await sent.delete()
    except TelegramAPIError:
        pass
