"""
db.py — async Supabase client and helpers that turn database errors into AppError.

Usage:
    rows = await run(db().table("products").select("*").eq("is_active", True))
    order = await rpc("create_order", {...})
"""
import json
import logging
from typing import Any

from postgrest.exceptions import APIError
from supabase import AsyncClient, acreate_client

from api.config import SUPABASE_KEY, SUPABASE_URL
from api.errors import DB_ERROR_STATUS, AppError

logger = logging.getLogger(__name__)

_client: AsyncClient | None = None


async def connect() -> None:
    global _client
    _client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)


def db() -> AsyncClient:
    if _client is None:
        raise RuntimeError("Database client not initialised — call db.connect() on startup")
    return _client


def _to_app_error(e: APIError) -> AppError:
    code, message = e.code or "", e.message or ""

    # Business errors raised by the SQL functions: message is the machine code.
    if code == "P0001" and message in DB_ERROR_STATUS:
        detail: dict[str, Any] = {}
        if e.details:
            try:
                detail = json.loads(e.details)
            except (TypeError, ValueError):
                pass
        return AppError(DB_ERROR_STATUS[message], message, detail=detail)

    if code == "23505":  # unique_violation
        return AppError(409, "CONFLICT", "Already exists", {"db": e.details or message})
    if code in ("23514", "23502", "22P02", "23503"):
        # check / not-null / bad uuid or number / missing referenced row
        return AppError(422, "VALIDATION_ERROR", message)

    logger.error("Database error %s: %s (%s)", code, message, e.details)
    return AppError(500, "SERVER_ERROR", "Database error")


async def run(query: Any) -> list[dict[str, Any]]:
    """Execute a PostgREST query builder; returns the rows."""
    try:
        res = await query.execute()
    except APIError as e:
        raise _to_app_error(e) from e
    return res.data or []


async def run_count(query: Any) -> tuple[list[dict[str, Any]], int]:
    """Execute a query built with count="exact"; returns (rows, total)."""
    try:
        res = await query.execute()
    except APIError as e:
        raise _to_app_error(e) from e
    return res.data or [], res.count or 0


async def rpc(fn: str, params: dict[str, Any]) -> Any:
    """Call a database function (db/schema.sql)."""
    try:
        res = await db().rpc(fn, params).execute()
    except APIError as e:
        raise _to_app_error(e) from e
    return res.data


async def first(query: Any) -> dict[str, Any] | None:
    rows = await run(query.limit(1))
    return rows[0] if rows else None
