import logging

from fastapi import APIRouter, HTTPException, Path, UploadFile, File, BackgroundTasks

from api.database import (
    create_payment,
    get_payment_by_id,
    get_order_payments,
    confirm_payment,
    upload_receipt_to_storage,
    receipt_url_prefix,
    get_order_by_id,
    get_customer,
)
from api.schemas.payment import CreatePaymentRequest, PaymentResponse, ConfirmPaymentResponse
from api.middleware.auth import AdminKey, TelegramUser
from api.utils.notify import notify_admin_new_payment, notify_customer_payment_confirmed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
# Orders in these states still accept a payment ("confirmed" = admin saw the order).
_PAYABLE_ORDER_STATUSES = {"pending", "confirmed"}
# An order with a payment in one of these states must not get another one.
_ACTIVE_PAYMENT_STATUSES = {"pending_verification", "verified"}


@router.post("/upload-receipt")
async def upload_receipt(
    telegram_id: TelegramUser,
    file: UploadFile = File(...),
) -> dict:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail={"error": f"Unsupported file type: {file.content_type}", "code": "VALIDATION_ERROR"},
        )
    content = await file.read(_MAX_SIZE + 1)
    if len(content) > _MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"error": "File too large (max 10 MB)", "code": "VALIDATION_ERROR"},
        )
    url = await upload_receipt_to_storage(
        file_bytes=content,
        content_type=file.content_type,
    )
    if not url:
        raise HTTPException(status_code=500, detail={"error": "Failed to upload receipt", "code": "SERVER_ERROR"})
    return {"url": url}


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment_record(
    body: CreatePaymentRequest,
    background_tasks: BackgroundTasks,
    telegram_id: TelegramUser,
) -> PaymentResponse:
    order = await get_order_by_id(body.order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"error": "Order not found", "code": "NOT_FOUND"})

    # Verify order belongs to authenticated customer
    customer = await get_customer(telegram_id)
    if not customer or order.get("customer_id") != customer.get("id"):
        raise HTTPException(status_code=403, detail={"error": "Access denied", "code": "FORBIDDEN"})

    if order.get("status") not in _PAYABLE_ORDER_STATUSES:
        raise HTTPException(status_code=409, detail={"error": "Order cannot be paid", "code": "CONFLICT"})
    existing = await get_order_payments(body.order_id)
    if any(p.get("status") in _ACTIVE_PAYMENT_STATUSES for p in existing):
        raise HTTPException(status_code=409, detail={"error": "Payment already submitted", "code": "CONFLICT"})

    # Only accept receipts uploaded through /payments/upload-receipt.
    if body.receipt_file_id and not body.receipt_file_id.startswith(receipt_url_prefix()):
        raise HTTPException(status_code=400, detail={"error": "Invalid receipt URL", "code": "VALIDATION_ERROR"})

    payment = await create_payment(
        order_id=body.order_id,
        method=body.method,
        amount=float(order["total_amount"]),
        receipt_file_id=body.receipt_file_id or "",
    )
    if not payment:
        raise HTTPException(status_code=500, detail={"error": "Failed to create payment", "code": "SERVER_ERROR"})

    customers_data = order.get("customers") or {}
    background_tasks.add_task(
        notify_admin_new_payment,
        payment=payment,
        order=order,
        customer={
            "full_name": customers_data.get("full_name", "—"),
            "phone": customers_data.get("phone", "—"),
            "telegram_id": customers_data.get("telegram_id", ""),
        },
    )

    return PaymentResponse(
        id=payment["id"],
        order_id=payment["order_id"],
        method=payment["method"],
        status=payment["status"],
        amount=float(payment["amount"]),
        receipt_file_id=payment.get("receipt_file_id"),
        paid_at=payment.get("paid_at"),
    )


@router.patch("/{payment_id}/confirm", response_model=ConfirmPaymentResponse, dependencies=[AdminKey])
async def confirm_payment_endpoint(
    background_tasks: BackgroundTasks,
    payment_id: str = Path(...),
) -> ConfirmPaymentResponse:
    payment = await get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail={"error": "Payment not found", "code": "NOT_FOUND"})
    if payment["status"] == "verified":
        raise HTTPException(status_code=409, detail={"error": "Payment already confirmed", "code": "CONFLICT"})

    updated = await confirm_payment(payment_id)
    if not updated:
        raise HTTPException(status_code=500, detail={"error": "Failed to confirm payment", "code": "SERVER_ERROR"})

    order = await get_order_by_id(payment["order_id"])
    if order:
        customers_data = order.get("customers") or {}
        tg_id = customers_data.get("telegram_id", "")
        language = customers_data.get("language", "uz")
        if tg_id:
            background_tasks.add_task(
                notify_customer_payment_confirmed,
                telegram_id=tg_id,
                order_id=payment["order_id"],
                language=language,
            )

    return ConfirmPaymentResponse(
        id=payment_id,
        status="verified",
        order_id=payment["order_id"],
        message="Payment confirmed and customer notified",
    )
