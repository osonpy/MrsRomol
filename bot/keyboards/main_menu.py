"""
keyboards/main_menu.py — reply keyboards for the main navigation layer.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.messages import get_message


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """4-button persistent reply keyboard shown after language selection."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_message("btn_catalog", lang)),
                KeyboardButton(text=get_message("btn_my_orders", lang)),
            ],
            [
                KeyboardButton(text=get_message("btn_contact", lang)),
                KeyboardButton(text=get_message("btn_language", lang)),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for initial language selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский",   callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English",   callback_data="lang:en"),
            ]
        ]
    )
