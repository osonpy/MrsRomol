"""Bot texts in Uzbek and Russian."""

GREETING = {
    "uz": "Assalomu alaykum, {name}! 🌸\n\n<b>Mrs Romol</b> — roʻmollar va liboslar doʻkoniga xush kelibsiz.\nDoʻkonni quyidagi tugma orqali oching 👇",
    "ru": "Здравствуйте, {name}! 🌸\n\nДобро пожаловать в <b>Mrs Romol</b> — магазин платков и платьев.\nОткройте магазин кнопкой ниже 👇",
}
OPEN_SHOP = {"uz": "🛍 Doʻkonni ochish", "ru": "🛍 Открыть магазин"}
MENU_BUTTON = "Doʻkon"


def lang_of(language_code: str | None) -> str:
    return "ru" if (language_code or "").startswith("ru") else "uz"
