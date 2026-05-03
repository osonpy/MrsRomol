"""
keyboards/catalog.py — inline keyboards for product browsing.
"""
from __future__ import annotations

import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import PRODUCTS_PER_PAGE
from bot.messages import get_message
from bot.utils.formatters import format_price


def catalog_page_keyboard(
    products: list[dict],
    current_page: int,
    total_count: int,
    lang: str,
) -> InlineKeyboardMarkup:
    """
    Build a paginated product list keyboard.
    Each product gets its own button row; navigation arrows appear at the bottom.
    """
    total_pages = math.ceil(total_count / PRODUCTS_PER_PAGE) if total_count else 1
    rows = []

    # One button per product
    for p in products:
        stock_icon = "✅" if p["stock_qty"] > 0 else "❌"
        label = f"{stock_icon} {p['name']} — {format_price(p['sell_price'])} UZS"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"product:{p['id']}")]
        )

    # Pagination row
    nav_row: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(
                text=get_message("btn_prev", lang),
                callback_data=f"catalog_page:{current_page - 1}",
            )
        )
    nav_row.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop",  # Page indicator — not clickable
        )
    )
    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text=get_message("btn_next", lang),
                callback_data=f"catalog_page:{current_page + 1}",
            )
        )

    rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_detail_keyboard(product_id: str, lang: str, in_stock: bool) -> InlineKeyboardMarkup:
    """Keyboard shown under a product detail view."""
    rows = []
    if in_stock:
        rows.append(
            [
                InlineKeyboardButton(
                    text=get_message("btn_order_now", lang),
                    callback_data=f"order_product:{product_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=get_message("btn_back", lang),
                callback_data="catalog_page:1",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
