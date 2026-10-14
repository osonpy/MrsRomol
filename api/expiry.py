"""
expiry.py — background loop: cancel orders whose payment timer ran out and
tell the customers. Runs inside the API process (one uvicorn worker).
"""
import asyncio
import logging

from api import notify
from api.config import EXPIRY_CHECK_INTERVAL
from api.db import db, rpc, run

logger = logging.getLogger(__name__)


async def expire_once() -> int:
    expired = await rpc("expire_orders", {}) or []
    if not expired:
        return 0
    customers = await run(
        db().table("customers").select("id, telegram_id, language")
        .in_("id", list({o["customer_id"] for o in expired}))
    )
    by_id = {c["id"]: c for c in customers}
    for order in expired:
        c = by_id.get(order["customer_id"])
        if c:
            await notify.customer_order_update(c["telegram_id"], c["language"], order, "expired")
    logger.info("Expired %d unpaid order(s): %s", len(expired), [o["number"] for o in expired])
    return len(expired)


async def run_forever() -> None:
    while True:
        try:
            await expire_once()
        except asyncio.CancelledError:
            raise
        except Exception as e:  # keep the loop alive; next tick retries
            logger.error("expire_orders failed: %s", e)
        await asyncio.sleep(EXPIRY_CHECK_INTERVAL)
