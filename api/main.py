import logging
import sys

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import ALLOWED_ORIGINS
from api.routers import products, customers, orders, payments, internal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Misr Romol API",
    description="REST API for the Misr Romol Telegram Mini App",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(internal.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "code": "ERROR"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "SERVER_ERROR"},
    )


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "misr-romol-api"}


@app.get("/", tags=["health"])
async def root() -> dict:
    return {"message": "Misr Romol API", "docs": "/docs"}
