"""
schemas.py — request bodies. Responses are plain dicts shaped in the routers.
"""
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from api.constants import REGION_CODES, delivery_methods_for

Language = Literal["uz", "ru"]
Text = lambda n: Field(default="", max_length=n)  # noqa: E731

_PHONE = r"^\+?[0-9 ()-]{7,20}$"


def normalize_phone(v: str) -> str:
    """'+998 (90) 123-45-67' → '+998901234567'; 9 local digits get +998."""
    digits = "".join(ch for ch in v if ch.isdigit())
    if len(digits) == 9:
        digits = "998" + digits
    return "+" + digits


# ── customer ──────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    phone: Optional[str] = Field(default=None, pattern=_PHONE)
    language: Optional[Language] = None
    notify_new_products: Optional[bool] = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: Optional[str]) -> Optional[str]:
        return normalize_phone(v) if v else v


class CartItem(BaseModel):
    variant_id: UUID
    quantity: int = Field(ge=1, le=100)


class QuoteRequest(BaseModel):
    items: list[CartItem] = Field(min_length=1, max_length=50)
    promo_code: Optional[str] = Field(default=None, max_length=32)


class DeliveryInfo(BaseModel):
    contact_name: str = Field(min_length=1, max_length=128)
    contact_phone: str = Field(pattern=_PHONE)
    region: str
    district: str = Text(100)
    address: str = Field(min_length=1, max_length=500)
    location_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    location_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    delivery_method: Literal["taxi", "post", "bts"]
    customer_note: str = Text(1000)

    @field_validator("contact_phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("region")
    @classmethod
    def _known_region(cls, v: str) -> str:
        if v not in REGION_CODES:
            raise ValueError("unknown region")
        return v

    @model_validator(mode="after")
    def _method_fits_region(self) -> "DeliveryInfo":
        if self.delivery_method not in delivery_methods_for(self.region):
            raise ValueError("delivery method not available for this region")
        return self


class CreateOrderRequest(QuoteRequest):
    delivery: DeliveryInfo


# ── admin: catalogue ──────────────────────────────────────────────────────────

class SizeChart(BaseModel):
    columns: list[str] = Field(min_length=1, max_length=10)
    rows: list[dict[str, Any]] = Field(min_length=1, max_length=30)


class CategoryIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{1,64}$")
    name_uz: str = Field(min_length=1, max_length=100)
    name_ru: str = Field(min_length=1, max_length=100)
    sort_order: int = 0
    is_active: bool = True


class CategoryPatch(BaseModel):
    slug: Optional[str] = Field(default=None, pattern=r"^[a-z0-9-]{1,64}$")
    name_uz: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name_ru: Optional[str] = Field(default=None, min_length=1, max_length=100)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ProductIn(BaseModel):
    category_id: Optional[UUID] = None
    name_uz: str = Field(min_length=1, max_length=200)
    name_ru: str = Text(200)
    description_uz: str = Text(5000)
    description_ru: str = Text(5000)
    price: int = Field(ge=0, le=1_000_000_000)
    cost_price: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    size_chart: Optional[SizeChart] = None
    is_active: bool = True


class ProductPatch(BaseModel):
    category_id: Optional[UUID] = None
    name_uz: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name_ru: Optional[str] = Field(default=None, max_length=200)
    description_uz: Optional[str] = Field(default=None, max_length=5000)
    description_ru: Optional[str] = Field(default=None, max_length=5000)
    price: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    cost_price: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    size_chart: Optional[SizeChart] = None
    is_active: Optional[bool] = None


class VariantIn(BaseModel):
    color_uz: Optional[str] = Field(default=None, max_length=50)
    color_ru: Optional[str] = Field(default=None, max_length=50)
    color_hex: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    size: Optional[str] = Field(default=None, max_length=20)
    sku: Optional[str] = Field(default=None, max_length=64)
    stock: int = Field(default=0, ge=0, le=100_000)
    price_override: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    sort_order: int = 0
    is_active: bool = True


class VariantPatch(BaseModel):
    color_uz: Optional[str] = Field(default=None, max_length=50)
    color_ru: Optional[str] = Field(default=None, max_length=50)
    color_hex: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    size: Optional[str] = Field(default=None, max_length=20)
    sku: Optional[str] = Field(default=None, max_length=64)
    stock: Optional[int] = Field(default=None, ge=0, le=100_000)
    price_override: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ImageOrder(BaseModel):
    image_ids: list[UUID] = Field(min_length=1, max_length=5)


class ImagePatch(BaseModel):
    color_uz: Optional[str] = Field(default=None, max_length=50)


# ── admin: orders ─────────────────────────────────────────────────────────────

class ReviewPaymentRequest(BaseModel):
    approve: bool
    reason: str = Text(500)


class AdvanceOrderRequest(BaseModel):
    to: Literal["shipped", "delivered"]
    tracking_number: str = Text(64)
    delivery_info: str = Text(1000)
    note: str = Text(500)


class AdminCancelRequest(BaseModel):
    note: str = Text(500)


class OrderNotePatch(BaseModel):
    admin_note: str = Field(max_length=2000)


class DeliveryInfoRequest(BaseModel):
    delivery_info: str = Field(max_length=1000)


# ── admin: promo, cards, settings, staff ──────────────────────────────────────

class PromoIn(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{3,32}$")
    discount_type: Literal["percent", "fixed"]
    discount_value: int = Field(gt=0, le=1_000_000_000)
    min_order_amount: int = Field(default=0, ge=0)
    max_uses: Optional[int] = Field(default=None, gt=0)
    per_customer_limit: int = Field(default=1, gt=0)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    is_active: bool = True

    @model_validator(mode="after")
    def _percent_max_100(self) -> "PromoIn":
        if self.discount_type == "percent" and self.discount_value > 100:
            raise ValueError("percent discount must be 1–100")
        self.code = self.code.upper()
        return self


class PromoPatch(BaseModel):
    is_active: Optional[bool] = None
    max_uses: Optional[int] = Field(default=None, gt=0)
    ends_at: Optional[str] = None


class CardIn(BaseModel):
    card_number: str = Field(pattern=r"^[0-9 ]{16,19}$")
    holder_name: str = Field(min_length=1, max_length=100)
    card_type: Literal["uzcard", "humo", "visa", "mastercard"]
    sort_order: int = 0
    is_active: bool = True

    @field_validator("card_number")
    @classmethod
    def _digits_only(cls, v: str) -> str:
        digits = v.replace(" ", "")
        if len(digits) != 16:
            raise ValueError("card number must have 16 digits")
        return digits


class CardPatch(BaseModel):
    holder_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class SettingsPatch(BaseModel):
    reservation_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    rules_uz: Optional[str] = Field(default=None, max_length=5000)
    rules_ru: Optional[str] = Field(default=None, max_length=5000)


class StaffRoleRequest(BaseModel):
    role: Literal["customer", "seller", "admin"]
