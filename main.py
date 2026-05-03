"""
main.py — bot entry point.

Responsibilities:
  1. Configure logging.
  2. Build the Bot + Dispatcher.
  3. Register all routers in the correct priority order.
  4. Start polling.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import start, catalog, orders, payments, my_orders, admin

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ── Fallback / catch-all handler (must be last) ───────────────────────────────
from aiogram import Router, F
from aiogram.types import Message
from bot.database import get_customer
from bot.messages import get_message
from bot.keyboards.main_menu import main_menu_keyboard

_fallback_router = Router()

@_fallback_router.message()
async def fallback_handler(message: Message) -> None:
    """
    Catch all unhandled messages.
    Show the main menu again with a friendly nudge.
    """
    customer = await get_customer(str(message.from_user.id))
    lang = customer.get("language", "uz") if customer else "uz"
    await message.answer(
        get_message("unexpected_input", lang),
        reply_markup=main_menu_keyboard(lang) if customer else None,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Bootstrap
# ══════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # MemoryStorage is fine for development.
    # For production swap with RedisStorage to survive restarts.
    dp = Dispatcher(storage=MemoryStorage())

    # ── Register routers — ORDER MATTERS ──────────────────────────────────────
    # More specific routers first; fallback router last.
    dp.include_router(start.router)       # /start, /settings, language callbacks
    dp.include_router(admin.router)        # admin order/payment actions + /setphotos
    dp.include_router(catalog.router)     # catalog browsing + product detail
    dp.include_router(orders.router)      # order creation FSM
    dp.include_router(payments.router)    # receipt photo upload
    dp.include_router(my_orders.router)   # order history + contact
    dp.include_router(_fallback_router)   # catch-all — must be LAST

    logger.info("🤖 Misr Romol Bot starting...")

    # Drop any pending updates accumulated while the bot was offline
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
