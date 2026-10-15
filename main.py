"""
main.py — Telegram bot entry point.

The bot is small: /start opens the Mini App, the chat menu button opens the
Mini App, and admins approve or reject receipts with buttons. Everything else
(catalogue, orders, notifications) lives in the Mini App and the API.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from api import db
from bot.config import BOT_TOKEN, MINI_APP_URL
from bot.handlers import payments, start
from bot.texts import MENU_BUTTON

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def setup_bot(bot: Bot) -> None:
    """Menu button → Mini App, and the command list. Telegram needs HTTPS for Mini Apps."""
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Doʻkonni ochish")])
        await bot.set_my_commands([BotCommand(command="start", description="Открыть магазин")], language_code="ru")
        if MINI_APP_URL.startswith("https://"):
            await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text=MENU_BUTTON, web_app=WebAppInfo(url=MINI_APP_URL)))
        else:
            logger.warning("MINI_APP_URL is not HTTPS (%s): menu button not set", MINI_APP_URL)
    except Exception as e:  # cosmetic: never stop the bot for this
        logger.warning("Bot setup failed: %s", e)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await db.connect()

    dp = Dispatcher()
    dp.include_router(payments.router)
    dp.include_router(start.router)  # greets on any message — keep last

    await setup_bot(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Mrs Romol bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
