from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from .core.config import get_settings
from .core.database import create_tables
from .api.v1.router import api_router

settings = get_settings()

app = FastAPI(
    title="Digital Library API",
    version="1.0.0"
)

origins = settings.BACKEND_CORS_ORIGINS.split(",") if settings.BACKEND_CORS_ORIGINS else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    # create_tables()  # normally handled by alembic, but defined in database.py

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "details": str(exc)},
    )

app.include_router(api_router, prefix="/api/v1")
