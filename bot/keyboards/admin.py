"""
keyboards/admin.py — inline keyboards sent to the admin group.

Callback data format (max 64 bytes):
  adm_oc:{order_id}   → admin order confirm
  adm_ox:{order_id}   → admin order cancel
  adm_pv:{order_id}   → admin payment verify
  adm_pr:{order_id}   → admin payment reject
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Buttons sent with every new order notification to the admin group."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"adm_oc:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"adm_ox:{order_id}",
                ),
            ]
        ]
    )


def admin_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Buttons sent with every payment receipt notification to the admin group."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ To'lov tasdiqlandi",
                    callback_data=f"adm_pv:{order_id}",
                ),
                InlineKeyboardButton(
                    text="❌ To'lov rad etildi",
                    callback_data=f"adm_pr:{order_id}",
                ),
            ]
        ]
    )
