from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class CustomerRegisterRequest(BaseModel):
    telegram_id: str
    full_name: str
    language: str = "uz"
    phone: Optional[str] = None


class CustomerUpdateRequest(BaseModel):
    phone: Optional[str] = None
    language: Optional[str] = None
    full_name: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    telegram_id: str
    full_name: str
    phone: Optional[str] = None
    language: str = "uz"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
