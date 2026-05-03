"""
handlers/catalog.py — product browsing with photo support.

Fixes applied:
  1. callback.answer() called FIRST to prevent Telegram from retrying the callback
     (was causing duplicate product detail messages)
  2. Instead of deleting catalog msg, we EDIT it to product detail
     (cleaner UX, prevents stale-button issues from old messages)
"""
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from bot.database import get_customer, get_products_page, get_product_by_id, get_product_images
from bot.keyboards.catalog import catalog_page_keyboard, product_detail_keyboard
from bot.messages import get_message
from bot.utils.formatters import format_price, total_pages

logger = logging.getLogger(__name__)
router = Router()


async def _get_lang(telegram_id: str) -> str:
    customer = await get_customer(str(telegram_id))
    return customer.get("language", "uz") if customer else "uz"


# ── Catalog entry ──────────────────────────────────────────────────────────────

@router.message(F.text.func(lambda t: t and any(
    t == get_message("btn_catalog", lc) for lc in ["uz", "ru", "en"]
)))
async def msg_catalog(message: Message) -> None:
    lang = await _get_lang(message.from_user.id)
    await _send_catalog_page(message, lang, page=1, edit=False)


# ── Pagination ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("catalog_page:"))
async def cb_catalog_page(callback: CallbackQuery) -> None:
    # Acknowledge immediately to prevent Telegram retry
    await callback.answer()
    lang = await _get_lang(callback.from_user.id)
    page = int(callback.data.split(":")[1])
    await _send_catalog_page(callback.message, lang, page=page, edit=True)


# ── Product detail ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("product:"))
async def cb_product_detail(callback: CallbackQuery, bot: Bot) -> None:
    """
    FIX: callback.answer() is called FIRST.
    This tells Telegram 'received', preventing it from retrying the callback
    which caused duplicate product detail messages.

    UX: We EDIT the catalog message instead of delete+send.
    If photos exist (2-3), we send new messages after editing.
    """
    # ★ Answer immediately — prevents duplicate callback delivery
    await callback.answer()

    lang = await _get_lang(callback.from_user.id)
    product_id = callback.data.split(":")[1]

    product = await get_product_by_id(product_id)
    if not product:
        return

    in_stock = product["stock_qty"] > 0
    stock_label = (
        get_message("in_stock", lang) if in_stock
        else get_message("out_of_stock", lang)
    )
    detail_text = get_message(
        "product_detail", lang,
        name=product["name"],
        category=product.get("category") or "—",
        price=format_price(product["sell_price"]),
        stock=f"{product['stock_qty']} ({stock_label})",
        description=product.get("description") or "—",
    )
    keyboard = product_detail_keyboard(product_id, lang, in_stock)
    images = await get_product_images(product_id)

    if not images:
        # No photos — edit the catalog message in-place (no duplicate possible)
        try:
            await callback.message.edit_text(
                detail_text, reply_markup=keyboard, parse_mode="HTML"
            )
        except Exception:
            # Message can't be edited (e.g. too old) — send new one
            await callback.message.answer(
                detail_text, reply_markup=keyboard, parse_mode="HTML"
            )

    elif len(images) == 1:
        # Single photo — delete catalog, send photo with caption+button
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=images[0]["file_id"],
            caption=detail_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    else:
        # 2-3 photos — delete catalog, send media group, then button row
        try:
            await callback.message.delete()
        except Exception:
            pass
        media_group = [
            InputMediaPhoto(
                media=img["file_id"],
                caption=detail_text if i == 0 else None,
                parse_mode="HTML" if i == 0 else None,
            )
            for i, img in enumerate(images)
        ]
        await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=get_message("btn_order_now", lang) + " 👆",
            reply_markup=keyboard,
        )


# ── noop ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ── Internal helper ────────────────────────────────────────────────────────────

async def _send_catalog_page(message: Message, lang: str, page: int, edit: bool) -> None:
    products, total_count = await get_products_page(page)

    if not products and page == 1:
        text = get_message("no_products", lang)
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    tp = total_pages(total_count)
    text = get_message("catalog_header", lang, page=page, total_pages=tp)
    keyboard = catalog_page_keyboard(products, page, total_count, lang)

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
