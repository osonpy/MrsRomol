"""
keyboards/orders.py — inline keyboards used during the order creation FSM flow.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.messages import get_message


def delivery_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Pickup vs. home delivery choice."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_message("btn_pickup", lang),
                    callback_data="delivery:pickup",
                ),
                InlineKeyboardButton(
                    text=get_message("btn_delivery", lang),
                    callback_data="delivery:home",
                ),
            ]
        ]
    )


def order_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Confirm / Cancel order summary."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_message("btn_confirm", lang),
                    callback_data="order_confirm:yes",
                ),
                InlineKeyboardButton(
                    text=get_message("btn_cancel", lang),
                    callback_data="order_confirm:no",
                ),
            ]
        ]
    )
