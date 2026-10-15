"""
Receipt buttons in Telegram (bot/handlers/payments.py), driven with fake
callback queries against the real database.
"""
from types import SimpleNamespace as NS

from aiogram.types import ReplyKeyboardRemove

from bot.handlers.payments import on_payment_button
from conftest import OWNER, As
from helpers import make_product, order_with_receipt

STRANGER, BUYER = 4001, 4002


class FakeMessage:
    def __init__(self, chat_id: int):
        self.chat = NS(id=chat_id)
        self.photo = [object()]
        self.html_text = "💳 <b>Chek keldi</b>"
        self.edits: list[dict] = []

    async def edit_caption(self, caption, reply_markup=None):
        self.edits.append({"caption": caption, "markup": reply_markup})

    async def edit_text(self, text, reply_markup=None):
        self.edits.append({"caption": text, "markup": reply_markup})

    async def edit_reply_markup(self, reply_markup=None):
        self.edits.append({"caption": None, "markup": reply_markup})


def press(client, user_id: int, data: str, message: FakeMessage, name="Makhmud") -> list:
    answers = []

    async def answer(text=None, show_alert=False):
        answers.append((text, show_alert))

    cb = NS(
        data=data,
        from_user=NS(id=user_id, first_name=name, last_name=None, language_code="uz"),
        message=message,
        answer=answer,
    )
    client.portal.call(on_payment_button, cb)
    return answers


def buttons(markup) -> list[str]:
    if markup is None:
        return []
    return [b.callback_data or b.url or "" for row in markup.inline_keyboard for b in row]


def test_receipt_buttons_flow(client, fakes):
    owner, buyer = As(client, OWNER, "Makhmud"), As(client, BUYER, "Xaridor")
    p = make_product(owner, name="Bot sinov roʻmol", stock=5)
    order = order_with_receipt(buyer, p["variants"][0]["id"])
    pay = order["payment"]["id"]
    msg = FakeMessage(-100500)

    # a stranger can't decide
    ans = press(client, STRANGER, f"pay:ok:{pay}", msg, name="Begona")
    assert ans == [("Bu tugmalar faqat adminlar uchun", True)]
    assert buyer.get(f"/orders/{order['id']}").json()["status"] == "payment_review"

    # "Reject" shows reasons, "Back" restores the two buttons
    press(client, OWNER, f"pay:no:{pay}", msg)
    assert len(msg.edits[-1]["markup"].inline_keyboard) == 5
    assert buttons(msg.edits[-1]["markup"])[0] == f"pay:r:0:{pay}"
    press(client, OWNER, f"pay:back:{pay}", msg)
    assert buttons(msg.edits[-1]["markup"]) == [f"pay:ok:{pay}", f"pay:no:{pay}"]

    # approve: order confirmed, buyer told, message shows who approved
    before = len(fakes.sent)
    ans = press(client, OWNER, f"pay:ok:{pay}", msg)
    assert ans[-1] == ("Tasdiqlandi ✅", False)
    assert buyer.get(f"/orders/{order['id']}").json()["status"] == "confirmed"
    assert any(m["chat_id"] == BUYER and "tasdiqlandi" in m["text"] for m in fakes.sent[before:])
    assert "✅ <b>Tasdiqlandi</b> — Makhmud" in msg.edits[-1]["caption"]
    assert "startapp=admin_order_" in buttons(msg.edits[-1]["markup"])[0]

    # the same receipt in another admin chat: already decided
    other = FakeMessage(OWNER)
    ans = press(client, OWNER, f"pay:no:{pay}", other)  # opening reasons is harmless
    ans = press(client, OWNER, f"pay:r:0:{pay}", other)
    assert ans == [("Bu chek allaqachon koʻrib chiqilgan", True)]
    assert other.edits[-1]["markup"] is None
    assert buyer.get(f"/orders/{order['id']}").json()["status"] == "confirmed"


def test_reject_with_reason(client, fakes):
    owner, buyer = As(client, OWNER, "Makhmud"), As(client, BUYER, "Xaridor")
    p = make_product(owner, name="Bot sinov roʻmol 2", stock=5)
    order = order_with_receipt(buyer, p["variants"][0]["id"])
    msg = FakeMessage(-100500)

    before = len(fakes.sent)
    press(client, OWNER, f"pay:r:1:{order['payment']['id']}", msg)
    got = buyer.get(f"/orders/{order['id']}").json()
    assert got["cancel_reason"] == "payment_rejected" and got["payment"]["reject_reason"] == "Summa mos emas"
    assert any(m["chat_id"] == BUYER and "Summa mos emas" in m["text"] for m in fakes.sent[before:])
    assert "❌ <b>Rad etildi</b>: Summa mos emas" in msg.edits[-1]["caption"]
    assert owner.get(f"/admin/products/{p['id']}").json()["total_stock"] == 5  # stock returned


def test_bad_callback_data_is_rejected(client):
    ans = press(client, OWNER, "pay:r:99:00000000-0000-0000-0000-000000000000", FakeMessage(OWNER))
    assert ans == [("Notoʻgʻri tugma", True)]


def test_greeting_offers_the_shop_only_in_private_chats(client):
    from bot.handlers.start import greet

    replies, removed, deleted = [], [], []

    async def delete():
        deleted.append(True)

    async def answer(text, reply_markup=None):
        if isinstance(reply_markup, ReplyKeyboardRemove):  # clears the old bot's keyboard
            removed.append(text)
        else:
            replies.append((text, reply_markup))
        return NS(delete=delete)

    def message(chat_type, lang):
        return NS(chat=NS(type=chat_type), from_user=NS(first_name="Zarina<b>", language_code=lang), answer=answer)

    client.portal.call(greet, message("private", "ru"))
    text, markup = replies[-1]
    assert "Здравствуйте, Zarina&lt;b&gt;" in text  # name escaped
    assert markup.inline_keyboard[0][0].web_app.url == "https://app.test"
    client.portal.call(greet, message("private", "uz"))
    assert "Mrs Romol" in replies[-1][0] and replies[-1][1].inline_keyboard[0][0].text == "🛍 Doʻkonni ochish"
    client.portal.call(greet, message("supergroup", "uz"))
    assert len(replies) == 2  # silent in the admin group
    assert len(removed) == len(deleted) == 2  # old reply keyboard removed, helper message deleted


def test_bot_profile_is_synced_only_when_it_differs():
    import asyncio

    from main import sync_profile
    from bot.texts import BOT_NAME, DESCRIPTION, SHORT_DESCRIPTION

    class FakeBot:
        def __init__(self):
            self.store, self.sets = {}, []

        def _get(self, kind, field):
            async def get(language_code=None):
                return NS(**{field: self.store.get((kind, language_code), "")})
            return get

        def _set(self, kind, field):
            async def set_(language_code=None, **kw):
                self.sets.append((kind, language_code))
                self.store[(kind, language_code)] = kw[field]
            return set_

        def __getattr__(self, attr):
            kind = attr.split("_my_")[1]
            field = "name" if kind == "name" else kind
            return self._get(kind, field) if attr.startswith("get") else self._set(kind, field)

    bot = FakeBot()
    asyncio.run(sync_profile(bot))
    assert len(bot.sets) == 6  # name, short and full description × default (uz) and ru
    assert bot.store[("name", None)] == BOT_NAME
    assert bot.store[("short_description", "ru")] == SHORT_DESCRIPTION["ru"]
    assert bot.store[("description", None)] == DESCRIPTION["uz"]
    assert all(len(t) <= 120 for t in SHORT_DESCRIPTION.values()) and all(len(t) <= 512 for t in DESCRIPTION.values())

    asyncio.run(sync_profile(bot))
    assert len(bot.sets) == 6  # nothing changed → nothing sent (Telegram rate-limits these)
