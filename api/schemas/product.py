from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    stock_qty: int = 0
    sell_price: float = 0.0
    image_file_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
