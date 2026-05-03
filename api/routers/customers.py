import logging

from fastapi import APIRouter, Depends, HTTPException

from api.database import get_customer, upsert_customer, update_customer_profile
from api.schemas.customer import CustomerRegisterRequest, CustomerUpdateRequest, CustomerResponse
from api.middleware.auth import TelegramUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/register", response_model=CustomerResponse)
async def register_customer(
    body: CustomerRegisterRequest,
    telegram_id: TelegramUser,
) -> CustomerResponse:
    if telegram_id != body.telegram_id:
        raise HTTPException(
            status_code=403,
            detail={"error": "telegram_id mismatch", "code": "VALIDATION_ERROR"},
        )
    customer = await upsert_customer(
        telegram_id=body.telegram_id,
        full_name=body.full_name,
        phone=body.phone or "",
        language=body.language,
    )
    if not customer:
        raise HTTPException(status_code=500, detail={"error": "Failed to register customer", "code": "SERVER_ERROR"})
    return CustomerResponse(**customer)


@router.get("/me", response_model=CustomerResponse)
async def get_my_profile(telegram_id: TelegramUser) -> CustomerResponse:
    customer = await get_customer(telegram_id)
    if not customer:
        raise HTTPException(status_code=404, detail={"error": "Customer not found", "code": "NOT_FOUND"})
    return CustomerResponse(**customer)


@router.patch("/me", response_model=CustomerResponse)
async def update_my_profile(
    body: CustomerUpdateRequest,
    telegram_id: TelegramUser,
) -> CustomerResponse:
    updated = await update_customer_profile(
        telegram_id=telegram_id,
        phone=body.phone,
        language=body.language,
        full_name=body.full_name,
    )
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "Customer not found", "code": "NOT_FOUND"})
    return CustomerResponse(**updated)
