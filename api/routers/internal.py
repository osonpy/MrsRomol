import logging

from fastapi import APIRouter, HTTPException

from api.middleware.auth import AdminKey
from api.schemas.payment import NotifyRequest
from api.utils.notify import send_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[AdminKey])


@router.post("/notify", status_code=200)
async def internal_notify(
    body: NotifyRequest,
) -> dict:
    success = await send_message(
        chat_id=body.chat_id,
        text=body.text,
        parse_mode=body.parse_mode,
    )
    if not success:
        raise HTTPException(
            status_code=502,
            detail={"error": "Failed to send Telegram message", "code": "UPSTREAM_ERROR"},
        )
    return {"ok": True}
