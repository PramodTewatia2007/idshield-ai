from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from app.core.config import settings
from app.core.init_db import init_db_and_seed
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.cases import router as cases_router
from app.api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage paths exist
    os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    os.makedirs(settings.SAMPLES_DIR, exist_ok=True)
    # Initialize DB & demo data
    await init_db_and_seed()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IDShield AI — AI-Based Fake Identity & Document Screening System with OSINT Integration",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directory for document image viewing
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "IDShield AI Backend API Service",
        "docs_url": "/docs",
        "version": settings.VERSION,
        "status": "online"
    }
