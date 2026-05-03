"""
api/models/schemas.py — Pydantic v2 request/response models for all endpoints.
"""
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED / ERROR
# ═══════════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    error: str
    code: str


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ═══════════════════════════════════════════════════════════════════════════════

class CustomerRegisterRequest(BaseModel):
    telegram_id: str
    full_name: str
    phone: str = ""
    language: str = "uz"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("uz", "ru", "en"):
            return "uz"
        return v


class CustomerUpdateRequest(BaseModel):
    phone: Optional[str] = None
    language: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("uz", "ru", "en"):
            return "uz"
        return v


class CustomerResponse(BaseModel):
    id: str
    telegram_id: str
    full_name: str
    phone: str
    language: str
    is_wholesale: bool = False
    created_at: str


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════

class ProductResponse(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    stock_qty: int
    sell_price: float
    wholesale_price: float
    is_active: bool
    primary_image: Optional[str] = None   # Telegram file_id of first image
    images: List[str] = Field(default_factory=list)  # all file_ids
    metadata: Optional[dict] = Field(default_factory=dict)  # {"colors": [...]}


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ═══════════════════════════════════════════════════════════════════════════════

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItemRequest] = Field(min_length=1)
    delivery_type: str = "pickup"
    address: str = ""
    notes: str = ""

    @field_validator("delivery_type")
    @classmethod
    def validate_delivery(cls, v: str) -> str:
        if v not in ("pickup", "delivery"):
            return "pickup"
        return v


class OrderItemResponse(BaseModel):
    id: Optional[str] = None
    product_id: str
    quantity: int
    unit_price: float
    product_name: Optional[str] = None


class PaymentBriefResponse(BaseModel):
    id: str
    method: str
    status: str
    amount: float
    paid_at: str


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    delivery_type: str
    total_amount: float
    notes: str
    source: str
    created_at: str
    items: List[OrderItemResponse] = Field(default_factory=list)
    payment: Optional[PaymentBriefResponse] = None


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]


# ═══════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class CreatePaymentRequest(BaseModel):
    order_id: str
    method: str = "card"
    amount: float = Field(gt=0)
    receipt_url: str = ""

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = ("card", "click", "payme", "cash")
        if v not in allowed:
            return "card"
        return v


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    method: str
    status: str
    amount: float
    receipt_url: str
    paid_at: str


class ConfirmPaymentResponse(BaseModel):
    id: str
    status: str
    order_id: str
    message: str = "Payment confirmed"


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL NOTIFY
# ═══════════════════════════════════════════════════════════════════════════════

class NotifyRequest(BaseModel):
    chat_id: int
    message: str
    parse_mode: str = "HTML"
