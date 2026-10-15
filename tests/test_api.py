"""
End-to-end walk through the shop: roles → catalogue → cart → order → payment
→ review → delivery, plus expiry, cancellation and access rules.
Tests run in file order and share state through S. This file expects an
empty database, so it must sort first (pytest runs files alphabetically).
"""
import io

from PIL import Image

from conftest import ALI, OWNER, VALI, WIFE, As, init_data, sql

S: dict = {}

DELIVERY = {
    "contact_name": "Ali Valiyev",
    "contact_phone": "+998 90 123 45 67",
    "region": "tashkent_city",
    "address": "Chilonzor 9, 12-uy",
    "delivery_method": "taxi",
}


def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (2400, 1800), (180, 140, 100)).save(buf, "PNG")
    return buf.getvalue()


JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def notes(fakes, chat_id):
    return [m for m in fakes.sent if m["chat_id"] == chat_id]


# ── auth & roles ──────────────────────────────────────────────────────────────

def test_auth_rejects_missing_bad_and_stale_init_data(client):
    assert client.get("/me").status_code == 422
    assert client.get("/me", headers={"X-Telegram-Init-Data": "user=x&hash=abc"}).status_code == 401
    stale = init_data(ALI, age=2 * 86400)
    r = client.get("/me", headers={"X-Telegram-Init-Data": stale})
    assert r.status_code == 401 and r.json()["code"] == "INVALID_INIT_DATA"


def test_first_visit_creates_customer_and_owner_is_super_admin(owner, ali, vali):
    assert owner.get("/me").json()["role"] == "super_admin"
    me = ali.get("/me").json()
    assert me["role"] == "customer" and me["full_name"] == "Ali" and me["language"] == "uz"
    assert vali.get("/me").json()["language"] == "ru"


def test_customer_cannot_use_admin_api(ali):
    r = ali.get("/admin/dashboard")
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"


def test_owner_appoints_admin(owner, wife):
    assert owner.put(f"/admin/staff/{WIFE}", json={"role": "admin"}).status_code == 404  # never opened the shop
    wife.get("/me")
    r = owner.put(f"/admin/staff/{WIFE}", json={"role": "admin"})
    assert r.status_code == 200 and r.json()["role"] == "admin"
    assert wife.get("/admin/dashboard").status_code == 200
    assert owner.put(f"/admin/staff/{OWNER}", json={"role": "customer"}).status_code == 403
    staff = owner.get("/admin/staff").json()["staff"]
    assert {s["telegram_id"] for s in staff} == {OWNER, WIFE}


def test_super_admin_finds_people_to_appoint(owner, wife, ali):
    found = owner.get("/admin/customers", params={"q": "ali"}).json()["customers"]
    assert [c["telegram_id"] for c in found] == [ALI]
    assert owner.get("/admin/customers", params={"q": str(WIFE)}).json()["customers"][0]["role"] == "admin"
    assert owner.get("/admin/customers", params={"q": "x,y)or(z"}).status_code == 200
    assert wife.get("/admin/customers").status_code == 403


def test_only_super_admin_manages_cards_and_settings(owner, wife):
    card = {"card_number": "8600 1234 5678 9012", "holder_name": "MAKHMUD", "card_type": "uzcard"}
    assert wife.post("/admin/payment-cards", json=card).status_code == 403
    r = owner.post("/admin/payment-cards", json=card)
    assert r.status_code == 201 and r.json()["card_number"] == "8600123456789012"
    S["card_id"] = r.json()["id"]
    assert wife.patch("/admin/settings", json={"reservation_minutes": 45}).status_code == 403
    r = owner.patch("/admin/settings", json={"rules_uz": "Sotilgan mahsulot qaytarilmaydi."})
    assert r.json()["rules_uz"] == "Sotilgan mahsulot qaytarilmaydi." and r.json()["reservation_minutes"] == 30


# ── catalogue (admin) ─────────────────────────────────────────────────────────

def test_admin_builds_catalogue(wife, fakes):
    r = wife.post("/admin/categories", json={"slug": "romollar", "name_uz": "Ro'mollar", "name_ru": "Платки"})
    assert r.status_code == 201
    S["cat"] = r.json()["id"]
    assert wife.post("/admin/categories", json={"slug": "romollar", "name_uz": "x", "name_ru": "x"}).status_code == 409

    r = wife.post("/admin/products", json={
        "category_id": S["cat"], "name_uz": "Ipak ro'mol", "name_ru": "Шёлковый платок", "price": 150000,
        "cost_price": 80000,
        "size_chart": {"columns": ["length"], "rows": [{"size": "M", "length": [140, 142]}]},
    })
    assert r.status_code == 201
    S["prod"] = r.json()["id"]

    r = wife.post(f"/admin/products/{S['prod']}/variants",
                  json={"color_uz": "Qora", "color_ru": "Чёрный", "color_hex": "#000000", "size": "M", "stock": 2})
    assert r.status_code == 201
    r = wife.post(f"/admin/products/{S['prod']}/variants",
                  json={"color_uz": "Oq", "color_ru": "Белый", "size": "L", "stock": 1, "price_override": 170000})
    p = r.json()
    assert p["total_stock"] == 3
    S["black"] = next(v["id"] for v in p["variants"] if v["color_uz"] == "Qora")
    S["white"] = next(v["id"] for v in p["variants"] if v["color_uz"] == "Oq")
    dup = wife.post(f"/admin/products/{S['prod']}/variants", json={"color_uz": "Qora", "size": "M"})
    assert dup.status_code == 409


def test_admin_uploads_photos_as_webp(wife, fakes):
    r = wife.post(f"/admin/products/{S['prod']}/images",
                  files=[("files", ("a.png", png_bytes(), "image/png"))], data={"color_uz": "Qora"})
    assert r.status_code == 201, r.text
    img = r.json()["images"][0]
    assert img["url"].endswith(".webp") and img["thumb_url"].endswith("_thumb.webp")
    stored = [k for k in fakes.files if k.startswith("product-images/")]
    assert len(stored) == 2
    large = Image.open(io.BytesIO(fakes.files[next(k for k in stored if not k.endswith("_thumb.webp"))][0]))
    assert large.format == "WEBP" and max(large.size) == 1600
    S["img"] = img["id"]

    bad = wife.post(f"/admin/products/{S['prod']}/images", files=[("files", ("x.png", b"not an image", "image/png"))])
    assert bad.status_code == 422
    six = [("files", (f"{i}.png", png_bytes(), "image/png")) for i in range(5)]
    assert wife.post(f"/admin/products/{S['prod']}/images", files=six).json()["code"] == "TOO_MANY_IMAGES"


def test_hidden_product_not_in_shop(wife, ali):
    r = wife.post("/admin/products", json={"name_uz": "Yashirin shapka", "price": 50000, "is_active": False})
    S["hidden"] = r.json()["id"]
    assert ali.get(f"/products/{S['hidden']}").status_code == 404


# ── shop ──────────────────────────────────────────────────────────────────────

def test_meta(ali):
    m = ali.get("/meta").json()
    assert m["me"]["role"] == "customer"
    assert [c["slug"] for c in m["categories"]] == ["romollar"]
    assert any(r["code"] == "tashkent_city" for r in m["regions"])
    assert m["reservation_minutes"] == 30 and m["rules"]["uz"]


def test_catalogue_listing_and_filters(ali):
    r = ali.get("/products").json()
    assert r["total"] == 1
    card = r["products"][0]
    assert card["price"] == 150000 and card["price_max"] == 170000
    assert card["in_stock"] and card["is_new"] and card["image"]["thumb_url"]
    assert {c["uz"] for c in card["colors"]} == {"Qora", "Oq"} and set(card["sizes"]) == {"M", "L"}
    assert "cost_price" not in card

    assert ali.get("/products", params={"size": "L"}).json()["total"] == 1
    assert ali.get("/products", params={"size": "XXL"}).json()["total"] == 0
    assert ali.get("/products", params={"color": "Oq", "size": "M"}).json()["total"] == 0
    assert ali.get("/products", params={"q": "ипак"}).json()["total"] == 0
    assert ali.get("/products", params={"q": "шёлк"}).json()["total"] == 1
    for spelling in ("ROMOL", "ro'mol", "ro‘mol", "roʻmol", "ro`mol", "ipak ro"):
        assert ali.get("/products", params={"q": spelling}).json()["total"] == 1, spelling
    assert ali.get("/products", params={"q": "a,b)or(x*"}).status_code == 200
    assert ali.get("/products", params={"category_id": S["cat"], "max_price": 100000}).json()["total"] == 0


def test_product_detail_hides_exact_stock(ali):
    p = ali.get(f"/products/{S['prod']}").json()
    assert p["size_chart"]["columns"] == ["length"]
    white = next(v for v in p["variants"] if v["id"] == S["white"])
    assert white["price"] == 170000 and white["in_stock"] and white["low_stock"]
    assert "stock" not in white


def test_favorites(ali, vali):
    assert ali.put(f"/favorites/{S['prod']}").status_code == 204
    assert ali.put(f"/favorites/{S['prod']}").status_code == 204  # idempotent
    assert [p["id"] for p in ali.get("/favorites").json()["products"]] == [S["prod"]]
    assert ali.get(f"/products/{S['prod']}").json()["is_favorite"]
    assert not vali.get(f"/products/{S['prod']}").json()["is_favorite"]
    assert ali.delete(f"/favorites/{S['prod']}").status_code == 204
    assert ali.get("/favorites").json()["products"] == []


def test_cart_quote_with_promo_and_stock_issue(wife, ali):
    r = wife.post("/admin/promo-codes", json={
        "code": "bahor10", "discount_type": "percent", "discount_value": 10, "min_order_amount": 200000,
    })
    assert r.status_code == 201 and r.json()["code"] == "BAHOR10"

    q = ali.post("/cart/quote", json={"items": [{"variant_id": S["black"], "quantity": 2},
                                                {"variant_id": S["white"], "quantity": 1}],
                                      "promo_code": "bahor10"}).json()
    assert q["subtotal"] == 470000 and q["discount"] == 47000 and q["total"] == 423000
    assert q["promo"]["valid"] and not q["issues"]

    q = ali.post("/cart/quote", json={"items": [{"variant_id": S["black"], "quantity": 1}],
                                      "promo_code": "BAHOR10"}).json()
    assert q["promo"] == {"code": "BAHOR10", "valid": False, "error_code": "PROMO_MIN_AMOUNT",
                          "detail": {"min_order_amount": 200000}}
    q = ali.post("/cart/quote", json={"items": [{"variant_id": S["white"], "quantity": 5}]}).json()
    assert q["issues"] == [{"variant_id": S["white"], "code": "OUT_OF_STOCK", "available": 1}]


# ── order → payment → review → delivery ───────────────────────────────────────

def test_order_validation(ali):
    bad_method = {**DELIVERY, "delivery_method": "post"}
    r = ali.post("/orders", json={"items": [{"variant_id": S["black"], "quantity": 1}], "delivery": bad_method})
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    r = ali.post("/orders", json={"items": [{"variant_id": S["black"], "quantity": 0}], "delivery": DELIVERY})
    assert r.status_code == 422
    r = ali.post("/orders", json={"items": [{"variant_id": S["white"], "quantity": 3}], "delivery": DELIVERY})
    assert r.status_code == 409 and r.json() == {
        "error": "Out of stock", "code": "OUT_OF_STOCK", "detail": {"variant_id": S["white"], "available": 1}}


def test_create_order(ali, fakes):
    before = len(fakes.sent)
    r = ali.post("/orders", json={
        "items": [{"variant_id": S["black"], "quantity": 2}, {"variant_id": S["white"], "quantity": 1}],
        "delivery": DELIVERY, "promo_code": "BAHOR10",
    })
    assert r.status_code == 201, r.text
    o = r.json()
    S["order"] = o["id"]
    assert o["number"] >= 1001 and o["status"] == "awaiting_payment" and o["total"] == 423000
    assert len(o["items"]) == 2 and o["items"][0]["image"]
    assert ali.get("/me").json()["phone"] == "+998901234567"  # normalised, remembered for next time

    new = fakes.sent[before:]
    assert {m["chat_id"] for m in new} == {-100500, OWNER, ALI}
    group = next(m for m in new if m["chat_id"] == -100500)
    assert f"#{o['number']}" in group["text"] and "423 000" in group["text"]
    assert f"startapp=admin_order_{o['id']}" in str(group["markup"])  # groups get a direct link
    assert "30 daqiqa" in next(m for m in new if m["chat_id"] == ALI)["text"]


def test_order_is_private(ali, vali):
    assert vali.get(f"/orders/{S['order']}").status_code == 404
    assert vali.post(f"/orders/{S['order']}/cancel").status_code == 404
    mine = ali.get(f"/orders/{S['order']}").json()
    assert mine["payment_cards"][0]["id"] == S["card_id"]
    assert "admin_note" not in mine and "customer" not in mine
    assert [o["id"] for o in ali.get("/orders").json()["orders"]] == [S["order"]]


def test_submit_payment(ali, vali, fakes):
    url = f"/orders/{S['order']}/payment"
    r = ali.post(url, files={"receipt": ("r.txt", b"hello", "text/plain")})
    assert r.status_code == 415
    r = ali.post(url, files={"receipt": ("r.jpg", b"GIF89a fake", "image/jpeg")})
    assert r.status_code == 422
    assert vali.post(url, files={"receipt": ("r.jpg", JPEG, "image/jpeg")}).status_code == 404
    assert not [k for k in fakes.files if k.startswith("receipts/")]  # nothing stored for rejected tries

    before = len(fakes.sent)
    r = ali.post(url, files={"receipt": ("r.jpg", JPEG, "image/jpeg")}, data={"card_id": S["card_id"]})
    assert r.status_code == 201, r.text
    o = r.json()
    assert o["status"] == "payment_review" and o["payment"]["amount"] == 423000
    assert "receipt_url" not in o["payment"]
    assert len([k for k in fakes.files if k.startswith("receipts/")]) == 1
    receipt_msg = next(m for m in fakes.sent[before:] if m["chat_id"] == OWNER and "Chek keldi" in m["text"])
    assert receipt_msg["method"] == "sendPhoto" and receipt_msg["photo"].startswith("https://signed.test/receipts/")
    buttons = [b["callback_data"] for row in receipt_msg["markup"]["inline_keyboard"] for b in row if "callback_data" in b]
    assert buttons == [f"pay:ok:{o['payment']['id']}", f"pay:no:{o['payment']['id']}"]  # handled by the bot

    again = ali.post(url, files={"receipt": ("r.jpg", JPEG, "image/jpeg")})
    assert again.status_code == 409 and again.json()["code"] == "INVALID_TRANSITION"


def test_admin_reviews_payment(wife, owner, ali, fakes):
    o = wife.get(f"/admin/orders/{S['order']}").json()
    assert o["payment"]["receipt_url"].startswith("https://signed.test/receipts/")
    assert o["customer"]["telegram_id"] == ALI
    pay = o["payment"]["id"]

    assert wife.post(f"/admin/payments/{pay}/review", json={"approve": False}).status_code == 422
    r = wife.post(f"/admin/payments/{pay}/review", json={"approve": True})
    assert r.status_code == 200 and r.json()["status"] == "confirmed"
    r = owner.post(f"/admin/payments/{pay}/review", json={"approve": False, "reason": "x"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_REVIEWED"
    assert "tasdiqlandi" in notes(fakes, ALI)[-1]["text"]

    d = wife.get("/admin/dashboard").json()
    assert d["to_ship"] == 1 and d["today"]["revenue"] == 423000
    assert {v["id"] for v in d["low_stock"]} >= {S["black"], S["white"]}


def test_admin_ships_and_delivers(wife, ali, fakes):
    url = f"/admin/orders/{S['order']}/advance"
    assert wife.post(url, json={"to": "delivered"}).json()["code"] == "INVALID_TRANSITION"
    info_url = f"/admin/orders/{S['order']}/delivery-info"
    assert wife.put(info_url, json={"delivery_info": "x"}).json()["code"] == "INVALID_TRANSITION"  # not shipped yet
    r = wife.post(url, json={"to": "shipped", "tracking_number": "BTS-777", "delivery_info": "Toshkent filiali <3"})
    assert r.json()["status"] == "shipped" and r.json()["delivery_info"] == "Toshkent filiali <3"
    msg = notes(fakes, ALI)[-1]["text"]
    assert "BTS-777" in msg and "Toshkent filiali &lt;3" in msg

    # The live-tracking link arrives after shipping: the customer sees it and gets a message.
    sent = len(notes(fakes, ALI))
    r = wife.put(info_url, json={"delivery_info": "Yandex Go: https://3.redirect.appmetrica.yandex.com/route?x=1"})
    assert r.status_code == 200
    assert ali.get(f"/orders/{S['order']}").json()["delivery_info"].startswith("Yandex Go: https://")
    assert len(notes(fakes, ALI)) == sent + 1 and "https://3.redirect" in notes(fakes, ALI)[-1]["text"]
    assert ali.put(info_url, json={"delivery_info": "hack"}).status_code == 403
    assert wife.put(f"/admin/orders/00000000-0000-0000-0000-000000000000/delivery-info", json={"delivery_info": "x"}).status_code == 404

    assert wife.post(url, json={"to": "delivered"}).json()["status"] == "delivered"
    assert wife.put(info_url, json={"delivery_info": "late"}).status_code == 409
    assert wife.patch(f"/admin/orders/{S['order']}", json={"admin_note": "Mijoz mamnun"}).json()["admin_note"]

    hist = ali.get(f"/orders/{S['order']}").json()["history"]
    assert [h["to_status"] for h in hist] == ["awaiting_payment", "payment_review", "confirmed", "shipped", "delivered"]
    assert wife.post(f"/admin/orders/{S['order']}/cancel", json={}).status_code == 409


def test_admin_order_list_and_search(wife):
    n = wife.get(f"/admin/orders/{S['order']}").json()["number"]
    assert wife.get("/admin/orders", params={"q": f"#{n}"}).json()["total"] == 1
    assert wife.get("/admin/orders", params={"q": "123 45"}).json()["total"] == 1
    assert wife.get("/admin/orders", params={"status": "delivered"}).json()["orders"][0]["items_count"] == 3
    assert wife.get("/admin/orders", params={"status": "nope"}).status_code == 422


# ── expiry, cancel, reject ────────────────────────────────────────────────────

def _restock(wife, qty=5):
    wife.patch(f"/admin/variants/{S['black']}", json={"stock": qty})


def test_unpaid_order_expires_and_stock_returns(client, wife, vali, fakes):
    import anyio

    from api import expiry

    _restock(wife)
    o = vali.post("/orders", json={"items": [{"variant_id": S["black"], "quantity": 2}],
                                   "delivery": {**DELIVERY, "region": "samarkand", "delivery_method": "bts"}}).json()
    assert wife.get(f"/admin/products/{S['prod']}").json()["total_stock"] == 3  # 5 - 2 reserved
    sql(f"update orders set expires_at = now() - interval '1 minute' where id = '{o['id']}'")

    assert client.portal.call(expiry.expire_once) == 1
    assert vali.get(f"/orders/{o['id']}").json()["cancel_reason"] == "expired"
    assert wife.get(f"/admin/products/{S['prod']}").json()["total_stock"] == 5
    assert "время оплаты истекло" in notes(fakes, VALI)[-1]["text"]  # Russian customer
    assert client.portal.call(expiry.expire_once) == 0
    late = vali.post(f"/orders/{o['id']}/payment", files={"receipt": ("r.jpg", JPEG, "image/jpeg")})
    assert late.status_code == 409


def test_customer_cancels_before_paying(vali, wife):
    o = vali.post("/orders", json={"items": [{"variant_id": S["black"], "quantity": 1}], "delivery": DELIVERY}).json()
    r = vali.post(f"/orders/{o['id']}/cancel")
    assert r.status_code == 200 and r.json()["cancel_reason"] == "by_customer"
    assert wife.get(f"/admin/products/{S['prod']}").json()["total_stock"] == 5


def test_rejected_payment_cancels_and_notifies(vali, wife, fakes):
    o = vali.post("/orders", json={"items": [{"variant_id": S["black"], "quantity": 1}], "delivery": DELIVERY}).json()
    vali.post(f"/orders/{o['id']}/payment", files={"receipt": ("r.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")})
    pay = wife.get(f"/admin/orders/{o['id']}").json()["payment"]["id"]
    r = wife.post(f"/admin/payments/{pay}/review", json={"approve": False, "reason": "Chek o'qilmaydi"})
    assert r.json()["cancel_reason"] == "payment_rejected"
    assert "Chek o&#x27;qilmaydi" in notes(fakes, VALI)[-1]["text"]
    assert wife.get(f"/admin/products/{S['prod']}").json()["total_stock"] == 5


# ── cleanup paths ─────────────────────────────────────────────────────────────

def test_delete_image_and_product_removes_files(wife, ali, fakes):
    assert wife.delete(f"/admin/images/{S['img']}").status_code == 204
    assert not [k for k in fakes.files if k.startswith("product-images/")]
    assert wife.delete(f"/admin/products/{S['hidden']}").status_code == 204
    # The delivered order still shows its items after the product is gone.
    assert wife.delete(f"/admin/products/{S['prod']}").status_code == 204
    items = ali.get(f"/orders/{S['order']}").json()["items"]
    assert {i["name_uz"] for i in items} == {"Ipak ro'mol"} and items[0]["image"] is None


# ── failures stay readable for the Mini App ───────────────────────────────────

ORIGIN = {"Origin": "https://app.test"}


def test_storage_failure_is_a_clean_502_with_cors(ali, wife, monkeypatch):
    import api.storage
    from types import SimpleNamespace

    class Broken:
        async def upload(self, *a, **k):
            raise RuntimeError("storage down")

    r = wife.post("/admin/products", json={"name_uz": "Sinov", "price": 1000})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    v = wife.post(f"/admin/products/{pid}/variants", json={"size": "M", "stock": 3}).json()["variants"][0]["id"]
    o = ali.post("/orders", json={"items": [{"variant_id": v, "quantity": 1}], "delivery": DELIVERY}).json()

    monkeypatch.setattr(api.storage, "db", lambda: SimpleNamespace(storage=SimpleNamespace(from_=lambda _: Broken())))
    r = ali.post(f"/orders/{o['id']}/payment", files={"receipt": ("r.jpg", JPEG, "image/jpeg")}, headers=ORIGIN)
    assert r.status_code == 502 and r.json()["code"] == "STORAGE_ERROR"
    assert r.headers["access-control-allow-origin"] == "https://app.test"
    assert ali.get(f"/orders/{o['id']}").json()["status"] == "awaiting_payment"  # nothing half-done


def test_unexpected_error_is_json_500_with_cors(ali, monkeypatch):
    import api.routers.shop

    async def boom():
        raise RuntimeError("unexpected")

    monkeypatch.setattr(api.routers.shop, "_settings", boom)
    r = ali.get("/meta", headers=ORIGIN)
    assert r.status_code == 500 and r.json()["code"] == "SERVER_ERROR"
    assert r.headers["access-control-allow-origin"] == "https://app.test"
