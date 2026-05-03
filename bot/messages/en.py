EN = {
    # --- Language selection ---
    "choose_language": "🌐 Tilni tanlang / Выберите язык / Choose language:",

    # --- Admin → Customer notifications ---
    "order_status_confirmed": (
        "✅ <b>Your order has been confirmed!</b>\n\n"
        "🆔 Order ID: <code>{order_id}</code>\n"
        "📊 Status: ✅ Confirmed\n\n"
        "We will contact you shortly."
    ),
    "order_status_cancelled": (
        "❌ <b>Your order has been cancelled.</b>\n\n"
        "🆔 Order ID: <code>{order_id}</code>\n\n"
        "For questions, contact us: /start → Contact Us"
    ),
    "payment_verified": (
        "💚 <b>Your payment has been verified!</b>\n\n"
        "🆔 Order ID: <code>{order_id}</code>\n"
        "📊 Status: 🚚 Preparing\n\n"
        "Your order will be delivered soon!"
    ),
    "payment_rejected": (
        "🔴 <b>Your payment was not verified.</b>\n\n"
        "🆔 Order ID: <code>{order_id}</code>\n\n"
        "Please resend the receipt photo or contact us."
    ),

    # --- Phone number request ---
    "ask_phone": (
        "👋 Hello, {name}!\n\n"
        "📱 To track your orders and contact you,\n"
        "please <b>share your phone number.</b>\n\n"
        "Tap the button below ↓"
    ),
    "ask_phone_retry": (
        "⚠️ Please <b>tap the button</b> to share your number\n"
        "or type it manually (e.g. +998901234567)"
    ),

    # --- Welcome ---
    "welcome": (
        "👋 Welcome, {name}!\n\n"
        "🏭 <b>Misr Romol</b> — your destination for premium Egyptian textile products!\n"
        "We offer the finest fabrics and scarves imported directly from Egypt."
    ),
    "welcome_back": "👋 Welcome back, {name}! How can I help you?",

    # --- Main menu ---
    "main_menu": "📋 Main menu — choose a section:",
    "btn_catalog": "🛍️ Catalog",
    "btn_my_orders": "📦 My Orders",
    "btn_contact": "📞 Contact Us",
    "btn_language": "🌐 Language",

    # --- Catalog ---
    "catalog_header": "🛍️ <b>Product Catalog</b>\nPage {page}/{total_pages}",
    "product_detail": (
        "📦 <b>{name}</b>\n"
        "🗂️ Category: {category}\n"
        "💰 Price: <b>{price} UZS</b>\n"
        "📊 In stock: {stock} pcs\n\n"
        "📝 {description}"
    ),
    "out_of_stock": "❌ Out of stock",
    "in_stock": "✅ In stock",
    "btn_order_now": "🛒 Order Now",
    "btn_back": "⬅️ Back",
    "btn_prev": "◀️ Previous",
    "btn_next": "Next ▶️",
    "no_products": "😔 No products available at the moment.",

    # --- Order flow ---
    "ask_quantity": "📦 How many pieces would you like? ({stock} in stock)",
    "invalid_quantity": "⚠️ Please enter a valid number (1 to {stock}).",
    "invalid_quantity_format": "⚠️ Please enter numbers only.",
    "ask_delivery": "🚚 Choose a delivery method:",
    "btn_pickup": "🏪 Pickup",
    "btn_delivery": "🚚 Home Delivery",
    "ask_address": "📍 Please enter your delivery address:",
    "order_summary": (
        "📋 <b>Order Summary</b>\n\n"
        "📦 Product: {product}\n"
        "🔢 Quantity: {quantity} pcs\n"
        "💰 Price: {price} UZS × {quantity} = <b>{total} UZS</b>\n"
        "🚚 Delivery: {delivery}\n"
        "{address_line}"
        "\n✅ Confirm your order?"
    ),
    "address_line": "📍 Address: {address}\n",
    "delivery_pickup": "Pickup",
    "delivery_home": "Home Delivery",
    "btn_confirm": "✅ Confirm",
    "btn_cancel": "❌ Cancel",
    "order_confirmed": (
        "🎉 <b>Order placed successfully!</b>\n\n"
        "🆔 Order ID: <code>{order_id}</code>\n"
        "📊 Status: ⏳ Pending\n\n"
        "Proceed to payment 👇"
    ),
    "order_cancelled": "❌ Order cancelled. You are back at the main menu.",
    "order_error": "⚠️ Failed to create order. Please try again.",
    "stock_depleted": "😔 Sorry, this product just ran out of stock. Please choose another.",

    # --- Payment ---
    "payment_instructions": (
        "💳 <b>Payment Details</b>\n\n"
        "💰 Amount: <b>{amount} UZS</b>\n"
        "🏦 Card number: <code>{card}</code>\n\n"
        "📸 After payment, send a <b>photo of your receipt</b> here."
    ),
    "receipt_received": (
        "✅ <b>Receipt received!</b>\n\n"
        "🔍 The admin will verify your payment shortly.\n"
        "📋 Order ID: <code>{order_id}</code>"
    ),
    "receipt_error": "⚠️ Failed to save receipt. Please send it again.",
    "send_photo_only": "📸 Please send a photo only.",

    # --- My orders ---
    "my_orders_header": "📦 <b>My Orders</b> (last 10):",
    "no_orders": "😔 You have no orders yet.",
    "order_item": (
        "🆔 <code>{order_id}</code>\n"
        "📅 {date}\n"
        "💰 {total} UZS\n"
        "📊 {status}\n"
        "─────────────────"
    ),
    "status_pending": "⏳ Pending",
    "status_confirmed": "✅ Confirmed",
    "status_shipped": "🚚 Shipped",
    "status_delivered": "📬 Delivered",
    "status_cancelled": "❌ Cancelled",

    # --- Contact ---
    "contact_info": (
        "📞 <b>Contact Information</b>\n\n"
        "📱 Phone: <a href='tel:+998901234567'>+998 90 123-45-67</a>\n"
        "📸 Instagram: <a href='https://instagram.com/msrromol'>@msrromol</a>\n"
        "✈️ Telegram: <a href='https://t.me/msrromol'>@msrromol</a>\n\n"
        "🕐 Working hours: Mon–Sat 09:00–18:00"
    ),

    # --- Settings ---
    "language_changed": "✅ Language changed!",

    # --- Errors ---
    "error_generic": "⚠️ An error occurred. Please press /start to restart.",
    "db_error": "🔴 Server connection issue. Please wait and try again.",
    "unexpected_input": "🤔 I didn't understand that. Please choose an option below:",

    # --- Admin notifications ---
    "admin_new_order": (
        "🛒 <b>NEW ORDER</b>\n\n"
        "👤 Customer: {customer_name}\n"
        "📱 Phone: {phone}\n"
        "🆔 Order: <code>{order_id}</code>\n\n"
        "📦 <b>Items:</b>\n{items}\n"
        "💰 Total: <b>{total} UZS</b>\n"
        "🚚 Delivery: {delivery}\n"
        "{address_line}"
        "📅 Date: {date}"
    ),
    "admin_new_payment": (
        "💳 <b>PAYMENT RECEIPT RECEIVED</b>\n\n"
        "👤 Customer: {customer_name}\n"
        "🆔 Order: <code>{order_id}</code>\n"
        "💰 Amount: {amount} UZS\n"
        "📅 Date: {date}\n\n"
        "👆 Check the receipt photo above"
    ),
}
