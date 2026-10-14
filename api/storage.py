"""
storage.py — product photos and payment receipts in Supabase Storage.

Product photos are re-encoded on upload: EXIF (incl. GPS) stripped, rotated
upright, and saved as WebP in two sizes — a large one for the product page and
a thumbnail for catalogue grids. Free Supabase has no on-the-fly resizing, so
we do it once here.
"""
import asyncio
import io
import logging
import uuid
from datetime import datetime, timezone

from PIL import Image, ImageOps, UnidentifiedImageError

from api.config import PRODUCT_IMAGES_BUCKET, RECEIPTS_BUCKET, SUPABASE_URL
from api.db import db
from api.errors import AppError, validation

logger = logging.getLogger(__name__)

MAX_PRODUCT_IMAGE_BYTES = 15 * 1024 * 1024
MAX_RECEIPT_BYTES = 10 * 1024 * 1024
RECEIPT_URL_TTL = 60 * 60  # signed receipt links live 1 hour

_LARGE, _THUMB = 1600, 600
_RECEIPT_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic"}
Image.MAX_IMAGE_PIXELS = 50_000_000  # refuse decompression bombs


async def _upload(bucket, path: str, data: bytes, options: dict) -> None:
    """Upload, turning any storage failure into a clean 502 for the client."""
    try:
        await bucket.upload(path, data, options)
    except Exception as e:
        logger.error("Storage upload %s failed: %s", path, e)
        raise AppError(502, "STORAGE_ERROR", "Could not store the file, please try again") from e


# ── product images ────────────────────────────────────────────────────────────

def product_image_urls(storage_path: str) -> dict[str, str]:
    base = f"{SUPABASE_URL}/storage/v1/object/public/{PRODUCT_IMAGES_BUCKET}/{storage_path}"
    return {"url": f"{base}.webp", "thumb_url": f"{base}_thumb.webp"}


def _encode_webp(data: bytes) -> tuple[bytes, bytes]:
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
            out = []
            for size in (_LARGE, _THUMB):
                copy = img.copy()
                copy.thumbnail((size, size), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                copy.save(buf, "WEBP", quality=82, method=6)  # no exif= → metadata dropped
                out.append(buf.getvalue())
            return out[0], out[1]
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise validation("Not a valid image") from e


async def upload_product_image(product_id: str, data: bytes) -> str:
    """Store a product photo; returns storage_path (without size suffix)."""
    if len(data) > MAX_PRODUCT_IMAGE_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "Image too large (max 15 MB)")
    large, thumb = await asyncio.to_thread(_encode_webp, data)
    path = f"{product_id}/{uuid.uuid4().hex}"
    bucket = db().storage.from_(PRODUCT_IMAGES_BUCKET)
    for name, body in ((f"{path}.webp", large), (f"{path}_thumb.webp", thumb)):
        # Fresh dict each time: storage3 pops "cache-control" out of the options.
        await _upload(bucket, name, body, {"content-type": "image/webp", "cache-control": "31536000"})
    return path


async def delete_product_images(storage_paths: list[str]) -> None:
    if not storage_paths:
        return
    files = [f"{p}{suffix}" for p in storage_paths for suffix in (".webp", "_thumb.webp")]
    try:
        await db().storage.from_(PRODUCT_IMAGES_BUCKET).remove(files)
    except Exception as e:  # orphaned files are harmless; don't fail the request
        logger.warning("Could not delete product images %s: %s", files, e)


# ── receipts ──────────────────────────────────────────────────────────────────

def _looks_like(content_type: str, data: bytes) -> bool:
    """Check the file really is the image type it claims (magic bytes)."""
    head = data[:16]
    return {
        "image/jpeg": head.startswith(b"\xff\xd8\xff"),
        "image/png": head.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": head[:4] == b"RIFF" and head[8:12] == b"WEBP",
        "image/heic": head[4:8] == b"ftyp",
    }.get(content_type, False)


async def upload_receipt(order_id: str, content_type: str, data: bytes) -> str:
    """Store a receipt in the private bucket; returns its storage path."""
    if content_type not in _RECEIPT_TYPES:
        raise AppError(415, "UNSUPPORTED_FILE", "Receipt must be JPEG, PNG, WebP or HEIC")
    if len(data) > MAX_RECEIPT_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "Receipt too large (max 10 MB)")
    if not _looks_like(content_type, data):
        raise validation("File content does not match its type")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = f"{day}/{order_id}/{uuid.uuid4().hex}.{_RECEIPT_TYPES[content_type]}"
    await _upload(db().storage.from_(RECEIPTS_BUCKET), path, data, {"content-type": content_type})
    return path


async def delete_receipt(path: str) -> None:
    try:
        await db().storage.from_(RECEIPTS_BUCKET).remove([path])
    except Exception as e:
        logger.warning("Could not delete receipt %s: %s", path, e)


async def receipt_signed_url(path: str) -> str | None:
    try:
        res = await db().storage.from_(RECEIPTS_BUCKET).create_signed_url(path, RECEIPT_URL_TTL)
    except Exception as e:
        logger.warning("Could not sign receipt %s: %s", path, e)
        return None
    return res.get("signedURL") or res.get("signedUrl")
