import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .api.v1.router import api_router
from .core.config import get_settings
from .core.rate_limit import limiter

settings = get_settings()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    # Schema is managed by Alembic (`alembic upgrade head`), not create_all().
    yield


app = FastAPI(title="Digital Library API", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full details server-side; never leak them to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


app.include_router(api_router, prefix="/api/v1")
