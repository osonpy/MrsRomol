"""Small builders shared by test files (each test file must run on its own)."""
import io

from PIL import Image

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
DELIVERY = {
    "contact_name": "Test Mijoz",
    "contact_phone": "+998 90 000 00 00",
    "region": "tashkent_city",
    "address": "Yunusobod 4",
    "delivery_method": "taxi",
}


def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (800, 1000), (200, 160, 150)).save(buf, "PNG")
    return buf.getvalue()


def make_product(admin, name="Sinov roʻmol", price=100_000, stock=10, publish=True, photo=True) -> dict:
    p = admin.post("/admin/products", json={"name_uz": name, "name_ru": name + " (ru)", "price": price, "is_active": publish}).json()
    p = admin.post(f"/admin/products/{p['id']}/variants", json={"size": "M", "stock": stock}).json()
    if photo:
        p = admin.post(f"/admin/products/{p['id']}/images", files=[("files", ("a.png", png_bytes(), "image/png"))]).json()
    return p


def order_with_receipt(customer, variant_id: str) -> dict:
    o = customer.post("/orders", json={"items": [{"variant_id": variant_id, "quantity": 1}], "delivery": DELIVERY}).json()
    return customer.post(f"/orders/{o['id']}/payment", files={"receipt": ("r.jpg", JPEG, "image/jpeg")}).json()
