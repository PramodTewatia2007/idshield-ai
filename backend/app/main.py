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

from fastapi.responses import FileResponse
from fastapi import HTTPException, Request

# Health check endpoint
@app.get("/health")
async def health():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

# Check for compiled frontend production build (unified single-service deployment)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = os.path.join(frontend_dist, "index.html")
    # If a browser requests the root page and frontend build is present, serve the SPA UI
    if "text/html" in accept and os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "IDShield AI Backend API Service",
        "docs_url": "/docs",
        "version": settings.VERSION,
        "status": "online"
    }

if os.path.isdir(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if (
            full_path.startswith("api")
            or full_path.startswith("storage")
            or full_path in ("docs", "redoc", "openapi.json")
        ):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not Found")


