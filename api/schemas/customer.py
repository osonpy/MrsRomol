from __future__ import annotations
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field

Language = Literal["uz", "ru", "en"]


class CustomerRegisterRequest(BaseModel):
    telegram_id: str = Field(max_length=32)
    full_name: str = Field(min_length=1, max_length=128)
    language: Language = "uz"
    phone: Optional[str] = Field(default=None, max_length=32)


class CustomerUpdateRequest(BaseModel):
    phone: Optional[str] = Field(default=None, max_length=32)
    language: Optional[Language] = None
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=128)


class CustomerResponse(BaseModel):
    id: str
    telegram_id: str
    full_name: str
    phone: Optional[str] = None
    language: str = "uz"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
