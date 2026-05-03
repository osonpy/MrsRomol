import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import RedirectResponse

from api.database import get_all_products, get_product_by_id, get_telegram_file_url
from api.schemas.product import ProductResponse, ProductListResponse
from api.middleware.auth import TelegramUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(telegram_id: TelegramUser) -> ProductListResponse:
    products = await get_all_products()
    return ProductListResponse(
        products=[ProductResponse(**p) for p in products],
        total=len(products),
    )


@router.get("/{product_id}/image/{sort_order}", include_in_schema=False)
async def proxy_product_image(
    product_id: str = Path(...),
    sort_order: int = Path(..., ge=0),
) -> RedirectResponse:
    """Resolves product image_file_id → Telegram CDN URL → 302 redirect. No auth required."""
    product = await get_product_by_id(product_id)
    if not product or not product.get("image_file_id"):
        raise HTTPException(status_code=404, detail={"error": "No image for this product", "code": "NOT_FOUND"})
    url = await get_telegram_file_url(product["image_file_id"])
    if not url:
        raise HTTPException(status_code=502, detail={"error": "Could not resolve image URL", "code": "UPSTREAM_ERROR"})
    return RedirectResponse(url=url, status_code=302)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(...),
    telegram_id: TelegramUser = None,
) -> ProductResponse:
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail={"error": "Product not found", "code": "NOT_FOUND"})
    return ProductResponse(**product)
