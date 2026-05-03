"""
Centralized message registry.
All bot text MUST be retrieved via get_message() — never hardcode strings in handlers.
"""
from bot.messages.uz import UZ
from bot.messages.ru import RU
from bot.messages.en import EN

MESSAGES: dict[str, dict] = {
    "uz": UZ,
    "ru": RU,
    "en": EN,
}

DEFAULT_LANG = "uz"


def get_message(key: str, lang: str, **kwargs) -> str:
    """
    Return the localized message for `key` in `lang`.
    Falls back to DEFAULT_LANG if key is missing in the requested lang.
    Applies str.format(**kwargs) if kwargs are provided.
    """
    lang_dict = MESSAGES.get(lang, MESSAGES[DEFAULT_LANG])
    # Graceful fallback: try the default lang if key missing in chosen lang
    text = lang_dict.get(key) or MESSAGES[DEFAULT_LANG].get(key, f"[{key}]")
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
