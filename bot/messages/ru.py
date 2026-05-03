RU = {
    # --- Language selection ---
    "choose_language": "🌐 Tilni tanlang / Выберите язык / Choose language:",

    # --- Admin → Customer notifications ---
    "order_status_confirmed": (
        "✅ <b>Ваш заказ подтверждён!</b>\n\n"
        "🆔 ID заказа: <code>{order_id}</code>\n"
        "📊 Статус: ✅ Подтверждён\n\n"
        "Скоро свяжемся с вами."
    ),
    "order_status_cancelled": (
        "❌ <b>Ваш заказ отменён.</b>\n\n"
        "🆔 ID заказа: <code>{order_id}</code>\n\n"
        "Если есть вопросы, свяжитесь: /start → Контакты"
    ),
    "payment_verified": (
        "💚 <b>Оплата подтверждена!</b>\n\n"
        "🆔 ID заказа: <code>{order_id}</code>\n"
        "📊 Статус: 🚚 Готовимся\n\n"
        "Скоро доставим!"
    ),
    "payment_rejected": (
        "🔴 <b>Оплата не подтверждена.</b>\n\n"
        "🆔 ID заказа: <code>{order_id}</code>\n\n"
        "Пожалуйста, отправьте чек ещё раз или свяжитесь с нами."
    ),

    # --- Phone number request ---
    "ask_phone": (
        "👋 Привет, {name}!\n\n"
        "📱 Для отслеживания заказов и связи с вами\n"
        "пожалуйста <b>поделитесь номером телефона.</b>\n\n"
        "Нажмите кнопку ниже ↓"
    ),
    "ask_phone_retry": (
        "⚠️ Пожалуйста, <b>нажмите кнопку</b> для отправки номера\n"
        "или введите номер вручную (напр.: +998901234567)"
    ),

    # --- Welcome ---
    "welcome": (
        "👋 Добро пожаловать, {name}!\n\n"
        "🏭 <b>Misr Romol</b> — магазин качественных египетских текстильных изделий!\n"
        "Мы предлагаем лучшие ткани и платки, импортированные из Египта."
    ),
    "welcome_back": "👋 С возвращением, {name}! Чем могу помочь?",

    # --- Main menu ---
    "main_menu": "📋 Главное меню — выберите нужный раздел:",
    "btn_catalog": "🛍️ Каталог",
    "btn_my_orders": "📦 Мои заказы",
    "btn_contact": "📞 Контакты",
    "btn_language": "🌐 Язык",

    # --- Catalog ---
    "catalog_header": "🛍️ <b>Каталог товаров</b>\nСтраница {page}/{total_pages}",
    "product_detail": (
        "📦 <b>{name}</b>\n"
        "🗂️ Категория: {category}\n"
        "💰 Цена: <b>{price} UZS</b>\n"
        "📊 На складе: {stock} шт.\n\n"
        "📝 {description}"
    ),
    "out_of_stock": "❌ Нет в наличии",
    "in_stock": "✅ В наличии",
    "btn_order_now": "🛒 Заказать",
    "btn_back": "⬅️ Назад",
    "btn_prev": "◀️ Назад",
    "btn_next": "Вперёд ▶️",
    "no_products": "😔 Товары пока отсутствуют.",

    # --- Order flow ---
    "ask_quantity": "📦 Сколько штук хотите заказать? (На складе: {stock} шт.)",
    "invalid_quantity": "⚠️ Пожалуйста, введите корректное число (от 1 до {stock}).",
    "invalid_quantity_format": "⚠️ Пожалуйста, введите только цифры.",
    "ask_delivery": "🚚 Выберите способ получения:",
    "btn_pickup": "🏪 Самовывоз",
    "btn_delivery": "🚚 Доставка",
    "ask_address": "📍 Введите адрес доставки:",
    "order_summary": (
        "📋 <b>Сводка заказа</b>\n\n"
        "📦 Товар: {product}\n"
        "🔢 Количество: {quantity} шт.\n"
        "💰 Цена: {price} UZS × {quantity} = <b>{total} UZS</b>\n"
        "🚚 Доставка: {delivery}\n"
        "{address_line}"
        "\n✅ Подтверждаете заказ?"
    ),
    "address_line": "📍 Адрес: {address}\n",
    "delivery_pickup": "Самовывоз",
    "delivery_home": "Доставка",
    "btn_confirm": "✅ Подтвердить",
    "btn_cancel": "❌ Отменить",
    "order_confirmed": (
        "🎉 <b>Заказ принят!</b>\n\n"
        "🆔 ID заказа: <code>{order_id}</code>\n"
        "📊 Статус: ⏳ Ожидает\n\n"
        "Перейдите к оплате 👇"
    ),
    "order_cancelled": "❌ Заказ отменён. Вы вернулись в главное меню.",
    "order_error": "⚠️ Ошибка при создании заказа. Попробуйте ещё раз.",
    "stock_depleted": "😔 Извините, товар закончился. Выберите другой товар.",

    # --- Payment ---
    "payment_instructions": (
        "💳 <b>Информация об оплате</b>\n\n"
        "💰 Сумма: <b>{amount} UZS</b>\n"
        "🏦 Номер карты: <code>{card}</code>\n\n"
        "📸 После оплаты отправьте <b>фото чека</b> сюда."
    ),
    "receipt_received": (
        "✅ <b>Чек получен!</b>\n\n"
        "🔍 Администратор проверит оплату. Ответим вам в ближайшее время.\n"
        "📋 ID заказа: <code>{order_id}</code>"
    ),
    "receipt_error": "⚠️ Ошибка сохранения чека. Попробуйте отправить ещё раз.",
    "send_photo_only": "📸 Пожалуйста, отправьте только фотографию.",

    # --- My orders ---
    "my_orders_header": "📦 <b>Мои заказы</b> (последние 10):",
    "no_orders": "😔 У вас пока нет заказов.",
    "order_item": (
        "🆔 <code>{order_id}</code>\n"
        "📅 {date}\n"
        "💰 {total} UZS\n"
        "📊 {status}\n"
        "─────────────────"
    ),
    "status_pending": "⏳ Ожидает",
    "status_confirmed": "✅ Подтверждён",
    "status_shipped": "🚚 В пути",
    "status_delivered": "📬 Доставлен",
    "status_cancelled": "❌ Отменён",

    # --- Contact ---
    "contact_info": (
        "📞 <b>Контактная информация</b>\n\n"
        "📱 Телефон: <a href='tel:+998901234567'>+998 90 123-45-67</a>\n"
        "📸 Instagram: <a href='https://instagram.com/msrromol'>@msrromol</a>\n"
        "✈️ Telegram: <a href='https://t.me/msrromol'>@msrromol</a>\n\n"
        "🕐 Часы работы: Пн-Сб 09:00–18:00"
    ),

    # --- Settings ---
    "language_changed": "✅ Язык изменён!",

    # --- Errors ---
    "error_generic": "⚠️ Произошла ошибка. Нажмите /start для перезапуска.",
    "db_error": "🔴 Проблема с подключением к серверу. Подождите и попробуйте снова.",
    "unexpected_input": "🤔 Не понял команду. Выберите один из вариантов ниже:",

    # --- Admin notifications ---
    "admin_new_order": (
        "🛒 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
        "👤 Клиент: {customer_name}\n"
        "📱 Телефон: {phone}\n"
        "🆔 Заказ: <code>{order_id}</code>\n\n"
        "📦 <b>Товары:</b>\n{items}\n"
        "💰 Итого: <b>{total} UZS</b>\n"
        "🚚 Доставка: {delivery}\n"
        "{address_line}"
        "📅 Дата: {date}"
    ),
    "admin_new_payment": (
        "💳 <b>ПОЛУЧЕН ЧЕК ОПЛАТЫ</b>\n\n"
        "👤 Клиент: {customer_name}\n"
        "🆔 Заказ: <code>{order_id}</code>\n"
        "💰 Сумма: {amount} UZS\n"
        "📅 Дата: {date}\n\n"
        "👆 Проверьте фото чека выше"
    ),
}
