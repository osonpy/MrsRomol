from __future__ import annotations
from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    order_id: str
    method: str  # "card" | "click" | "payme" | "cash"
    amount: float
    receipt_file_id: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    method: str
    status: str
    amount: float
    receipt_file_id: Optional[str] = None
    paid_at: Optional[datetime] = None


class ConfirmPaymentResponse(BaseModel):
    id: str
    status: str
    order_id: str
    message: str


class NotifyRequest(BaseModel):
    chat_id: Union[str, int]
    text: str
    parse_mode: str = "HTML"
