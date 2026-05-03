UZ = {
    # --- Language selection ---
    "choose_language": "🌐 Tilni tanlang / Выберите язык / Choose language:",

    # --- Admin → Customer notifications ---
    "order_status_confirmed": (
        "✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
        "🆔 Buyurtma ID: <code>{order_id}</code>\n"
        "📊 Holat: ✅ Tasdiqlangan\n\n"
        "Yaqin orada siz bilan bog'lanamiz."
    ),
    "order_status_cancelled": (
        "❌ <b>Buyurtmangiz bekor qilindi.</b>\n\n"
        "🆔 Buyurtma ID: <code>{order_id}</code>\n\n"
        "Savollar bo'lsa, biz bilan bog'laning: /start → Bog'lanish"
    ),
    "payment_verified": (
        "💚 <b>To'lovingiz tasdiqlandi!</b>\n\n"
        "🆔 Buyurtma ID: <code>{order_id}</code>\n"
        "📊 Holat: 🚚 Tayyorlanmoqda\n\n"
        "Tez orada yetkazib beramiz!"
    ),
    "payment_rejected": (
        "🔴 <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
        "🆔 Buyurtma ID: <code>{order_id}</code>\n\n"
        "Iltimos, to'lov chekini qaytadan yuboring yoki biz bilan bog'laning."
    ),

    # --- Phone number request ---
    "ask_phone": (
        "👋 Salom, {name}!\n\n"
        "📱 Buyurtmalaringizni kuzatish va siz bilan bog'lanish uchun\n"
        "<b>telefon raqamingizni ulashing.</b>\n\n"
        "Quyidagi tugmani bosing ↓"
    ),
    "ask_phone_retry": (
        "⚠️ Iltimos, <b>tugmani bosib</b> raqamingizni ulashing\n"
        "yoki to'liq raqamni yozing (masalan: +998901234567)"
    ),

    # --- Welcome ---
    "welcome": (
        "👋 Assalomu alaykum, {name}!\n\n"
        "🏭 <b>Misr Romol</b> — Misrning sifatli to'qimachilik mahsulotlari do'koniga xush kelibsiz!\n"
        "Biz Misrdan import qilingan eng yaxshi gazlamalar va ro'mollarni taklif qilamiz."
    ),
    "welcome_back": "👋 Xush kelibsiz, {name}! Siz uchun nima qila olaman?",

    # --- Main menu ---
    "main_menu": "📋 Asosiy menyu — kerakli bo'limni tanlang:",
    "btn_catalog": "🛍️ Katalog",
    "btn_my_orders": "📦 Mening buyurtmalarim",
    "btn_contact": "📞 Bog'lanish",
    "btn_language": "🌐 Til",

    # --- Catalog ---
    "catalog_header": "🛍️ <b>Mahsulotlar katalogi</b>\nSahifa {page}/{total_pages}",
    "product_detail": (
        "📦 <b>{name}</b>\n"
        "🗂️ Kategoriya: {category}\n"
        "💰 Narx: <b>{price} UZS</b>\n"
        "📊 Omborda: {stock} dona\n\n"
        "📝 {description}"
    ),
    "out_of_stock": "❌ Mahsulot tugagan",
    "in_stock": "✅ Mavjud",
    "btn_order_now": "🛒 Buyurtma berish",
    "btn_back": "⬅️ Orqaga",
    "btn_prev": "◀️ Oldingi",
    "btn_next": "Keyingi ▶️",
    "no_products": "😔 Hozircha mahsulotlar mavjud emas.",

    # --- Order flow ---
    "ask_quantity": "📦 Nechta dona olmoqchisiz? (Omborda {stock} dona mavjud)",
    "invalid_quantity": "⚠️ Iltimos, to'g'ri son kiriting (1 dan {stock} gacha).",
    "invalid_quantity_format": "⚠️ Iltimos, faqat raqam kiriting.",
    "ask_delivery": "🚚 Yetkazib berish turini tanlang:",
    "btn_pickup": "🏪 O'zim olaman",
    "btn_delivery": "🚚 Yetkazib berish",
    "ask_address": "📍 Yetkazib berish manzilini yozing:",
    "order_summary": (
        "📋 <b>Buyurtma xulosasi</b>\n\n"
        "📦 Mahsulot: {product}\n"
        "🔢 Miqdor: {quantity} dona\n"
        "💰 Narx: {price} UZS × {quantity} = <b>{total} UZS</b>\n"
        "🚚 Yetkazish: {delivery}\n"
        "{address_line}"
        "\n✅ Tasdiqlaysizmi?"
    ),
    "address_line": "📍 Manzil: {address}\n",
    "delivery_pickup": "O'zim olaman",
    "delivery_home": "Yetkazib berish",
    "btn_confirm": "✅ Tasdiqlash",
    "btn_cancel": "❌ Bekor qilish",
    "order_confirmed": (
        "🎉 <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        "🆔 Buyurtma ID: <code>{order_id}</code>\n"
        "📊 Holat: ⏳ Kutilmoqda\n\n"
        "To'lov bo'limiga o'ting 👇"
    ),
    "order_cancelled": "❌ Buyurtma bekor qilindi. Asosiy menyuga qaytdingiz.",
    "order_error": "⚠️ Buyurtma yaratishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
    "stock_depleted": "😔 Kechirasiz, mahsulot turib qoldi. Boshqa mahsulotni tanlang.",

    # --- Payment ---
    "payment_instructions": (
        "💳 <b>To'lov ma'lumotlari</b>\n\n"
        "💰 To'lov summasi: <b>{amount} UZS</b>\n"
        "🏦 Karta raqami: <code>{card}</code>\n\n"
        "📸 To'lovni amalga oshirgandan so'ng, <b>chek rasmini</b> shu yerga yuboring."
    ),
    "receipt_received": (
        "✅ <b>Chek qabul qilindi!</b>\n\n"
        "🔍 Admin tomonidan tekshiriladi. Tez orada javob beramiz.\n"
        "📋 Buyurtma ID: <code>{order_id}</code>"
    ),
    "receipt_error": "⚠️ Chekni saqlashda xatolik. Iltimos, qaytadan yuboring.",
    "send_photo_only": "📸 Iltimos, faqat rasm yuboring.",

    # --- My orders ---
    "my_orders_header": "📦 <b>Mening buyurtmalarim</b> (Oxirgi 10 ta):",
    "no_orders": "😔 Sizda hali buyurtmalar yo'q.",
    "order_item": (
        "🆔 <code>{order_id}</code>\n"
        "📅 {date}\n"
        "💰 {total} UZS\n"
        "📊 {status}\n"
        "─────────────────"
    ),
    "status_pending": "⏳ Kutilmoqda",
    "status_confirmed": "✅ Tasdiqlangan",
    "status_shipped": "🚚 Yo'lda",
    "status_delivered": "📬 Yetkazildi",
    "status_cancelled": "❌ Bekor qilindi",

    # --- Contact ---
    "contact_info": (
        "📞 <b>Bog'lanish ma'lumotlari</b>\n\n"
        "📱 Telefon: <a href='tel:+998901234567'>+998 90 123-45-67</a>\n"
        "📸 Instagram: <a href='https://instagram.com/msrromol'>@msrromol</a>\n"
        "✈️ Telegram: <a href='https://t.me/msrromol'>@msrromol</a>\n\n"
        "🕐 Ish vaqti: Du-Sh 09:00–18:00"
    ),

    # --- Settings ---
    "language_changed": "✅ Til o'zgartirildi!",

    # --- Errors ---
    "error_generic": "⚠️ Xatolik yuz berdi. Iltimos, /start buyrug'ini bosing.",
    "db_error": "🔴 Serverga ulanishda muammo. Biroz kutib, qaytadan urinib ko'ring.",
    "unexpected_input": "🤔 Bu buyruqni tushunmadim. Quyidagi tugmalardan birini tanlang:",

    # --- Admin notifications ---
    "admin_new_order": (
        "🛒 <b>YANGI BUYURTMA</b>\n\n"
        "👤 Mijoz: {customer_name}\n"
        "📱 Telefon: {phone}\n"
        "🆔 Buyurtma: <code>{order_id}</code>\n\n"
        "📦 <b>Mahsulotlar:</b>\n{items}\n"
        "💰 Jami: <b>{total} UZS</b>\n"
        "🚚 Yetkazish: {delivery}\n"
        "{address_line}"
        "📅 Sana: {date}"
    ),
    "admin_new_payment": (
        "💳 <b>TO'LOV CHEKI KELDI</b>\n\n"
        "👤 Mijoz: {customer_name}\n"
        "🆔 Buyurtma: <code>{order_id}</code>\n"
        "💰 Summa: {amount} UZS\n"
        "📅 Sana: {date}\n\n"
        "👆 Chek rasmini tekshiring"
    ),
}
