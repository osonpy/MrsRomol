import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import db, expiry
from api.config import ALLOWED_ORIGINS, DEV_MODE
from api.errors import AppError
from api.routers import admin_catalog, admin_orders, admin_settings, shop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    if DEV_MODE:
        logger.warning("DEV_MODE is ON: mock initData is accepted. Never enable this in production!")
    task = asyncio.create_task(expiry.run_forever())
    yield
    task.cancel()


app = FastAPI(
    title="Misr Romol API",
    description="REST API for the Misr Romol Telegram Mini App",
    version="3.0.0",
    lifespan=lifespan,
    # API docs only in development — no need to publish the API map in production.
    docs_url="/docs" if DEV_MODE else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DEV_MODE else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["X-Telegram-Init-Data", "Content-Type"],
)

app.include_router(shop.router)
app.include_router(admin_orders.router)
app.include_router(admin_catalog.router)
app.include_router(admin_settings.router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content=exc.body())


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request", "code": "VALIDATION_ERROR", "detail": {"fields": fields}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "ERROR")
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail), "code": code, "detail": {}})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "SERVER_ERROR", "detail": {}},
    )


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "misr-romol-api"}
