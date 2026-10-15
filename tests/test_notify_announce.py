"""New-product announcements to subscribers (POST /admin/products/{id}/announce)."""
from conftest import OWNER, As
from helpers import make_product

FAN, QUIET, GONE = 5001, 5002, 5003


def test_announce_new_product(client, fakes):
    owner = As(client, OWNER, "Makhmud")
    fan, quiet, gone = As(client, FAN, "Fan", "ru"), As(client, QUIET, "Quiet"), As(client, GONE, "Gone")
    for c in (fan, quiet, gone):
        c.get("/me")
    quiet.patch("/me", json={"notify_new_products": False})
    fakes.blocked.add(GONE)  # GONE has blocked the bot

    hidden = make_product(owner, name="Yashirin", publish=False)
    r = owner.post(f"/admin/products/{hidden['id']}/announce")
    assert r.status_code == 409 and r.json()["code"] == "NOT_PUBLISHED"
    no_photo = make_product(owner, name="Rasmsiz", photo=False)
    assert owner.post(f"/admin/products/{no_photo['id']}/announce").json()["code"] == "NO_IMAGE"
    empty = make_product(owner, name="Tugagan", stock=0)
    assert owner.post(f"/admin/products/{empty['id']}/announce").json()["code"] == "OUT_OF_STOCK"

    p = make_product(owner, name="Kashmir roʻmol", price=210_000)
    before = len(fakes.sent)
    r = owner.post(f"/admin/products/{p['id']}/announce")
    assert r.status_code == 200 and r.json()["announced_at"]
    sent = [m for m in fakes.sent[before:] if m["method"] == "sendPhoto"]
    to = {m["chat_id"] for m in sent}
    assert FAN in to and QUIET not in to
    fan_msg = next(m for m in sent if m["chat_id"] == FAN)
    assert "Новинка" in fan_msg["text"] and "Kashmir roʻmol (ru)" in fan_msg["text"] and "210 000" in fan_msg["text"]
    assert fan_msg["markup"]["inline_keyboard"][0][0]["web_app"]["url"].endswith(f"/product/{p['id']}")
    assert fan_msg["photo"].endswith(".webp")

    # Blocked users are unsubscribed; a second announcement is refused.
    assert gone.get("/me").json()["notify_new_products"] is False
    r = owner.post(f"/admin/products/{p['id']}/announce")
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_ANNOUNCED"


def test_customers_cannot_announce(client):
    owner, fan = As(client, OWNER, "Makhmud"), As(client, FAN, "Fan")
    p = make_product(owner, name="Boshqa roʻmol")
    assert fan.post(f"/admin/products/{p['id']}/announce").status_code == 403
