import logging

from fastapi import APIRouter, HTTPException, Header, Depends

from api.config import ADMIN_SECRET_KEY
from api.schemas.payment import NotifyRequest
from api.utils.notify import send_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"])


def _admin_only(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail={"error": "Forbidden", "code": "FORBIDDEN"},
        )


@router.post("/notify", status_code=200)
async def internal_notify(
    body: NotifyRequest,
    _: None = Depends(_admin_only),
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
