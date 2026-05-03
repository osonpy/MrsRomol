import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from api.database import (
    create_order_with_items,
    get_customer_orders,
    get_customer,
)
from api.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
    OrderItemResponse,
    PaymentBriefResponse,
    OrderListResponse,
)
from api.middleware.auth import TelegramUser
from api.utils.notify import notify_admin_new_order

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])


def _build_order_response(order: dict) -> OrderResponse:
    items = []
    for item in order.get("items", []):
        product_name = (
            item.get("product_name")
            or (item.get("products") or {}).get("name")
        )
        items.append(OrderItemResponse(
            id=item.get("id"),
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=float(item["unit_price"]),
            product_name=product_name,
        ))

    payment = None
    raw_pay = order.get("payment")
    if raw_pay:
        payment = PaymentBriefResponse(
            id=raw_pay["id"],
            method=raw_pay["method"],
            status=raw_pay["status"],
            amount=float(raw_pay["amount"]),
            paid_at=raw_pay.get("paid_at"),
        )

    return OrderResponse(
        id=order["id"],
        customer_id=order["customer_id"],
        status=order["status"],
        delivery_type=order["delivery_type"],
        address=order.get("address") or "",
        notes=order.get("notes") or "",
        total_amount=float(order["total_amount"]),
        source=order.get("source", "miniapp"),
        created_at=order.get("created_at"),
        items=items,
        payment=payment,
    )


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    body: CreateOrderRequest,
    background_tasks: BackgroundTasks,
    telegram_id: TelegramUser,
) -> OrderResponse:
    customer = await get_customer(telegram_id)
    if not customer:
        raise HTTPException(status_code=404, detail={"error": "Customer not found", "code": "NOT_FOUND"})

    order, error = await create_order_with_items(
        customer_id=customer["id"],
        items=[item.model_dump() for item in body.items],
        delivery_type=body.delivery_type,
        address=body.address or "",
        notes=body.notes or "",
    )

    if error:
        if "OUT_OF_STOCK" in error:
            raise HTTPException(
                status_code=409,
                detail={"error": error.split(":")[1] if ":" in error else "Insufficient stock", "code": "OUT_OF_STOCK"},
            )
        raise HTTPException(
            status_code=400,
            detail={"error": error, "code": "VALIDATION_ERROR"},
        )
    if not order:
        raise HTTPException(status_code=500, detail={"error": "Failed to create order", "code": "SERVER_ERROR"})

    background_tasks.add_task(
        notify_admin_new_order,
        order=order,
        customer=customer,
        items=order.get("items", []),
    )

    return _build_order_response(order)


@router.get("/mine", response_model=OrderListResponse)
async def list_my_orders(telegram_id: TelegramUser) -> OrderListResponse:
    customer = await get_customer(telegram_id)
    if not customer:
        raise HTTPException(status_code=404, detail={"error": "Customer not found", "code": "NOT_FOUND"})
    orders = await get_customer_orders(customer["id"], limit=20)
    return OrderListResponse(orders=[_build_order_response(o) for o in orders])
