"""Bot texts in Uzbek and Russian."""

GREETING = {
    "uz": "Assalomu alaykum, {name}! 🌸\n\n<b>Mrs Romol</b> — roʻmollar va liboslar doʻkoniga xush kelibsiz.\nDoʻkonni quyidagi tugma orqali oching 👇",
    "ru": "Здравствуйте, {name}! 🌸\n\nДобро пожаловать в <b>Mrs Romol</b> — магазин платков и платьев.\nОткройте магазин кнопкой ниже 👇",
}
OPEN_SHOP = {"uz": "🛍 Doʻkonni ochish", "ru": "🛍 Открыть магазин"}
MENU_BUTTON = "Doʻkon"

# Bot profile. "uz" is also the default for every other app language (Telegram
# has no Uzbek interface, so most Uzbek users run it in English or Russian).
BOT_NAME = "Mrs Romol"
SHORT_DESCRIPTION = {  # profile page and link previews, ≤120 chars
    "uz": "Roʻmollar, abaya va liboslar hamda ularga mos kiyimlar. Telegram ichida qulay doʻkon 🌸",
    "ru": "Платки, абаи и платья, а также всё к ним. Удобный магазин в Telegram 🌸",
}
DESCRIPTION = {  # empty chat, before the user presses Start, ≤512 chars
    "uz": (
        "Assalomu alaykum! Mrs Romolʼga xush kelibsiz 🌸\n\n"
        "Roʻmollar, abaya va liboslar hamda ularga mos kiyimlar — barchasi bitta qulay doʻkonda.\n\n"
        "🛍 Katalogdan tanlang\n"
        "💳 Karta orqali toʻlang va chekni yuboring\n"
        "🚚 Taksi, pochta yoki BTS orqali qabul qiling\n\n"
        "Boshlash uchun «Start» tugmasini bosing 👇"
    ),
    "ru": (
        "Здравствуйте! Добро пожаловать в Mrs Romol 🌸\n\n"
        "Платки, абаи и платья, а также всё к ним — в одном удобном магазине.\n\n"
        "🛍 Выберите в каталоге\n"
        "💳 Оплатите картой и отправьте чек\n"
        "🚚 Получите доставку такси, почтой или BTS\n\n"
        "Нажмите «Старт», чтобы начать 👇"
    ),
}


def lang_of(language_code: str | None) -> str:
    return "ru" if (language_code or "").startswith("ru") else "uz"
