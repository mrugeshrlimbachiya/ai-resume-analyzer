from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    APP_NAME: str = "AI Resume Analyzer"
    APP_ENV: str = "development"
    DEBUG: bool = True
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"
    DATABASE_URL: str = "sqlite+aiosqlite:///./resume_analyzer.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
