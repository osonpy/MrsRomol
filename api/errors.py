"""
errors.py — one error type for the whole API.

Every error response has the shape  {"error": str, "code": str, "detail": {...}}.
The Mini App switches on `code`; `error` is a human-readable English hint.
"""
from typing import Any, Optional


class AppError(Exception):
    def __init__(self, status: int, code: str, error: str = "", detail: Optional[dict[str, Any]] = None):
        super().__init__(code)
        self.status = status
        self.code = code
        self.error = error or code.replace("_", " ").capitalize()
        self.detail = detail or {}

    def body(self) -> dict[str, Any]:
        return {"error": self.error, "code": self.code, "detail": self.detail}


def not_found(what: str = "Not found") -> AppError:
    return AppError(404, "NOT_FOUND", what)


def forbidden(error: str = "Access denied") -> AppError:
    return AppError(403, "FORBIDDEN", error)


def validation(error: str, detail: Optional[dict[str, Any]] = None) -> AppError:
    return AppError(422, "VALIDATION_ERROR", error, detail)


# Codes raised by the database functions (db/schema.sql) → HTTP status.
DB_ERROR_STATUS: dict[str, int] = {
    "ORDER_NOT_FOUND": 404,
    "VARIANT_NOT_FOUND": 404,
    "PAYMENT_NOT_FOUND": 404,
    "CARD_NOT_FOUND": 404,
    "FORBIDDEN": 403,
    "OUT_OF_STOCK": 409,
    "PRODUCT_INACTIVE": 409,
    "INVALID_TRANSITION": 409,
    "ALREADY_REVIEWED": 409,
    "ORDER_EXPIRED": 409,
    "EMPTY_ORDER": 422,
    "TOO_MANY_ITEMS": 422,
    "INVALID_QUANTITY": 422,
    "INVALID_REASON": 422,
    "RECEIPT_REQUIRED": 422,
    "PROMO_INVALID": 422,
    "PROMO_EXHAUSTED": 422,
    "PROMO_ALREADY_USED": 422,
    "PROMO_MIN_AMOUNT": 422,
}
