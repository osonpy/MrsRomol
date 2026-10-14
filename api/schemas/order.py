from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class DeliveryType(str, Enum):
    pickup = "pickup"
    delivery = "delivery"


class OrderItemRequest(BaseModel):
    product_id: str = Field(max_length=64)
    quantity: int = Field(ge=1, le=100)


class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest] = Field(min_length=1, max_length=50)
    delivery_type: DeliveryType
    address: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=1000)


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
    paid_at: Optional[datetime] = None


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    delivery_type: str
    address: Optional[str] = None
    notes: Optional[str] = None
    total_amount: float
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    payment: Optional[PaymentBriefResponse] = None


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
