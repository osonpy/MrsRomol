"""
constants.py — delivery regions and the rule for which delivery method fits each.

Tashkent city → taxi (Yandex etc.). Everywhere else → post or BTS.
The customer pays the courier directly, so no delivery price is stored.
"""

REGIONS: list[dict[str, str]] = [
    {"code": "tashkent_city", "uz": "Toshkent shahri", "ru": "г. Ташкент"},
    {"code": "tashkent", "uz": "Toshkent viloyati", "ru": "Ташкентская область"},
    {"code": "andijan", "uz": "Andijon", "ru": "Андижан"},
    {"code": "bukhara", "uz": "Buxoro", "ru": "Бухара"},
    {"code": "fergana", "uz": "Farg'ona", "ru": "Фергана"},
    {"code": "jizzakh", "uz": "Jizzax", "ru": "Джизак"},
    {"code": "kashkadarya", "uz": "Qashqadaryo", "ru": "Кашкадарья"},
    {"code": "khorezm", "uz": "Xorazm", "ru": "Хорезм"},
    {"code": "namangan", "uz": "Namangan", "ru": "Наманган"},
    {"code": "navoi", "uz": "Navoiy", "ru": "Навои"},
    {"code": "samarkand", "uz": "Samarqand", "ru": "Самарканд"},
    {"code": "surkhandarya", "uz": "Surxondaryo", "ru": "Сурхандарья"},
    {"code": "syrdarya", "uz": "Sirdaryo", "ru": "Сырдарья"},
    {"code": "karakalpakstan", "uz": "Qoraqalpog'iston", "ru": "Каракалпакстан"},
]
REGION_CODES = {r["code"] for r in REGIONS}

DELIVERY_METHODS: list[dict[str, str]] = [
    {"code": "taxi", "uz": "Taksi (Yandex va b.)", "ru": "Такси (Яндекс и др.)"},
    {"code": "post", "uz": "Pochta", "ru": "Почта"},
    {"code": "bts", "uz": "BTS", "ru": "BTS"},
]


def delivery_methods_for(region: str) -> set[str]:
    return {"taxi"} if region == "tashkent_city" else {"post", "bts"}


ORDER_STATUSES = ("awaiting_payment", "payment_review", "confirmed", "shipped", "delivered", "cancelled")
