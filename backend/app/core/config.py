import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "IDShield AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "idshield-super-secret-production-key-change-in-env-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SQLite / Postgres Database URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./idshield.db"
    
    # Storage paths
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
    DOCUMENTS_DIR: str = os.path.join(STORAGE_DIR, "documents")
    REPORTS_DIR: str = os.path.join(STORAGE_DIR, "reports")
    SAMPLES_DIR: str = os.path.join(STORAGE_DIR, "samples")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    # External Connectors Mode
    DEMO_MODE: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
