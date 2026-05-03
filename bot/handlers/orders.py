"""
handlers/orders.py
Multi-step order creation flow using Aiogram FSM.

States:
  OrderFSM.waiting_quantity  → user types how many pieces
  OrderFSM.waiting_delivery  → user picks Pickup / Delivery via inline button
  OrderFSM.waiting_address   → user types delivery address (only for home delivery)
  OrderFSM.waiting_confirm   → user taps Confirm / Cancel on the summary
"""
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.config import ADMIN_GROUP_ID, PAYMENT_CARD
from bot.database import (
    get_customer,
    get_product_by_id,
    create_order,
    create_order_item,
    decrement_stock,
)
from bot.keyboards.admin import admin_order_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from bot.keyboards.orders import delivery_type_keyboard, order_confirm_keyboard
from bot.messages import get_message
from bot.utils.formatters import format_price

logger = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════════════════════════════════════
# FSM state group
# ══════════════════════════════════════════════════════════════════════════════

class OrderFSM(StatesGroup):
    waiting_quantity = State()
    waiting_delivery = State()
    waiting_address  = State()
    waiting_confirm  = State()


# ── Helper: resolve customer language ─────────────────────────────────────────

async def _get_customer(telegram_id: str) -> tuple[dict | None, str]:
    """Return (customer_dict, lang). lang defaults to 'uz' on error."""
    customer = await get_customer(str(telegram_id))
    lang = customer.get("language", "uz") if customer else "uz"
    return customer, lang


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 — Initiate order from product detail (callback: order_product:<id>)
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("order_product:"))
async def cb_start_order(callback: CallbackQuery, state: FSMContext) -> None:
    """
    User tapped 'Order Now' on a product detail card.

    FIX: callback.answer() called FIRST to prevent Telegram from retrying
    the callback, which caused state to be set multiple times in race conditions.
    FIX: state.clear() before set_state() ensures no stale data from a previous
    order flow interferes with the new one.
    """
    # ★ Answer immediately to stop Telegram retry timer
    await callback.answer()

    _, lang = await _get_customer(callback.from_user.id)
    product_id = callback.data.split(":")[1]

    product = await get_product_by_id(product_id)
    if not product:
        await callback.message.answer(get_message("error_generic", lang))
        return

    if product["stock_qty"] <= 0:
        await callback.message.answer(get_message("stock_depleted", lang))
        return

    # ★ Clear any leftover FSM data from a previous order before starting fresh
    await state.clear()
    await state.update_data(
        product_id=product_id,
        product_name=product["name"],
        sell_price=float(product["sell_price"]),
        stock_qty=int(product["stock_qty"]),
    )
    await state.set_state(OrderFSM.waiting_quantity)

    await callback.message.answer(
        get_message("ask_quantity", lang, stock=product["stock_qty"]),
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 — Quantity input
# ══════════════════════════════════════════════════════════════════════════════

@router.message(OrderFSM.waiting_quantity)
async def msg_quantity(message: Message, state: FSMContext) -> None:
    """Validate and store the quantity the user typed."""
    _, lang = await _get_customer(message.from_user.id)
    data = await state.get_data()
    stock_qty = data["stock_qty"]

    # Validate: must be a positive integer within stock bounds
    try:
        qty = int(message.text.strip())
        if qty < 1 or qty > stock_qty:
            raise ValueError
    except (ValueError, AttributeError):
        # Non-integer or out-of-range
        if not (message.text or "").strip().isdigit():
            await message.answer(get_message("invalid_quantity_format", lang))
        else:
            await message.answer(
                get_message("invalid_quantity", lang, stock=stock_qty)
            )
        return  # Stay in the same state

    await state.update_data(quantity=qty)
    await state.set_state(OrderFSM.waiting_delivery)

    await message.answer(
        get_message("ask_delivery", lang),
        reply_markup=delivery_type_keyboard(lang),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 — Delivery type selection
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(OrderFSM.waiting_delivery, F.data.startswith("delivery:"))
async def cb_delivery_type(callback: CallbackQuery, state: FSMContext) -> None:
    """User chose Pickup or Home Delivery."""
    _, lang = await _get_customer(callback.from_user.id)
    delivery_type = callback.data.split(":")[1]  # 'pickup' or 'home'

    await state.update_data(delivery_type=delivery_type)

    if delivery_type == "home":
        # Need to collect the address next
        await state.set_state(OrderFSM.waiting_address)
        await callback.message.answer(get_message("ask_address", lang))
    else:
        # Pickup — no address needed; jump straight to summary
        await state.update_data(address="")
        await state.set_state(OrderFSM.waiting_confirm)
        await _send_order_summary(callback.message, state, lang)

    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# Step 4 — Address input (home delivery only)
# ══════════════════════════════════════════════════════════════════════════════

@router.message(OrderFSM.waiting_address)
async def msg_address(message: Message, state: FSMContext) -> None:
    """Store the typed address and show order summary."""
    _, lang = await _get_customer(message.from_user.id)
    address = (message.text or "").strip()

    if not address:
        await message.answer(get_message("ask_address", lang))
        return

    await state.update_data(address=address)
    await state.set_state(OrderFSM.waiting_confirm)
    await _send_order_summary(message, state, lang)


# ══════════════════════════════════════════════════════════════════════════════
# Step 5 — Confirm or Cancel
# ══════════════════════════════════════════════════════════════════════════════

@router.callback_query(OrderFSM.waiting_confirm, F.data == "order_confirm:yes")
async def cb_confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    User confirmed the order.
    1. Re-check stock (atomic decrement).
    2. Create order + order_item rows.
    3. Show payment instructions.
    4. Notify admin group.
    """
    customer, lang = await _get_customer(callback.from_user.id)
    data = await state.get_data()

    product_id   = data["product_id"]
    product_name = data["product_name"]
    sell_price   = data["sell_price"]
    quantity     = data["quantity"]
    delivery_type = data["delivery_type"]
    address      = data.get("address", "")
    total_amount = sell_price * quantity

    # ── Atomic stock decrement ────────────────────────────────────────────────
    stock_ok = await decrement_stock(product_id, quantity)
    if not stock_ok:
        await callback.message.edit_text(get_message("stock_depleted", lang))
        await state.clear()
        await callback.answer()
        return

    # ── Create order row ──────────────────────────────────────────────────────
    notes = f"Delivery address: {address}" if address else ""
    order = await create_order(
        customer_id=customer["id"],
        delivery_type=delivery_type,
        total_amount=total_amount,
        notes=notes,
    )

    if not order:
        await callback.message.edit_text(get_message("order_error", lang))
        await state.clear()
        await callback.answer()
        return

    order_id = order["id"]

    # ── Create order_item row ─────────────────────────────────────────────────
    await create_order_item(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=sell_price,
    )

    # ── Persist order_id for the payment handler (next step) ─────────────────
    await state.update_data(order_id=order_id, total_amount=total_amount)

    # ── Confirm message to user ───────────────────────────────────────────────
    await callback.message.edit_text(
        get_message("order_confirmed", lang, order_id=order_id),
        parse_mode="HTML",
    )

    # ── Payment instructions ──────────────────────────────────────────────────
    await callback.message.answer(
        get_message(
            "payment_instructions",
            lang,
            amount=format_price(total_amount),
            card=PAYMENT_CARD,
        ),
        parse_mode="HTML",
    )

    # ── Admin notification ────────────────────────────────────────────────────
    delivery_label = get_message(
        "delivery_home" if delivery_type == "home" else "delivery_pickup", lang
    )
    address_line = (
        get_message("address_line", "ru", address=address) if address else ""
    )
    items_text = f"  • {product_name} × {quantity} шт. — {format_price(sell_price)} UZS"

    admin_text = get_message(
        "admin_new_order",
        "ru",  # Admin notifications always in Russian for consistency
        customer_name=customer.get("full_name", "—"),
        phone=customer.get("phone", "—"),
        order_id=order_id,
        items=items_text,
        total=format_price(total_amount),
        delivery=delivery_label,
        address_line=address_line,
        date=datetime.now().strftime("%d.%m.%Y %H:%M"),
    )

    try:
        await bot.send_message(
            ADMIN_GROUP_ID,
            admin_text,
            parse_mode="HTML",
            reply_markup=admin_order_keyboard(order_id),  # ✅/❌ action buttons
        )
    except Exception as e:
        logger.error("Admin notification failed: %s", e)

    # Keep FSM data (order_id, total_amount) for the payment handler
    # but clear the order-creation states
    await state.set_state(None)
    await callback.answer()


@router.callback_query(OrderFSM.waiting_confirm, F.data == "order_confirm:no")
async def cb_cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    """User cancelled — clear FSM and return to main menu."""
    _, lang = await _get_customer(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(get_message("order_cancelled", lang))
    await callback.message.answer(
        get_message("main_menu", lang),
        reply_markup=main_menu_keyboard(lang),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════════════════════
# Unexpected text while in any order FSM state
# ══════════════════════════════════════════════════════════════════════════════

@router.message(OrderFSM.waiting_delivery)
@router.message(OrderFSM.waiting_confirm)
async def msg_unexpected_in_order(message: Message) -> None:
    """Ignore free-text messages when we expect a button press."""
    _, lang = await _get_customer(message.from_user.id)
    await message.answer(get_message("unexpected_input", lang))


# ══════════════════════════════════════════════════════════════════════════════
# Internal: build and send the order summary message
# ══════════════════════════════════════════════════════════════════════════════

async def _send_order_summary(
    message: Message,
    state: FSMContext,
    lang: str,
) -> None:
    """Compose and send the order summary with Confirm/Cancel buttons."""
    data = await state.get_data()
    product_name  = data["product_name"]
    sell_price    = data["sell_price"]
    quantity      = data["quantity"]
    delivery_type = data["delivery_type"]
    address       = data.get("address", "")
    total         = sell_price * quantity

    delivery_label = get_message(
        "delivery_home" if delivery_type == "home" else "delivery_pickup", lang
    )
    address_line = (
        get_message("address_line", lang, address=address) if address else ""
    )

    text = get_message(
        "order_summary",
        lang,
        product=product_name,
        quantity=quantity,
        price=format_price(sell_price),
        total=format_price(total),
        delivery=delivery_label,
        address_line=address_line,
    )

    await message.answer(
        text,
        reply_markup=order_confirm_keyboard(lang),
        parse_mode="HTML",
    )
