import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    APP_NAME: str = "Golden Brown 3 - Legal Document RAG"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    VECTOR_STORE_PATH: Path = BASE_DIR / "vector_store"
    MAX_FILE_SIZE_MB: int = 50

    # RAG Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.35

    # Providers
    LLM_PROVIDER: str = "local"  # "local" | "ollama" | "openai"
    LLM_MODEL: str = "gemma4:e4b-it-q4_K_M"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "http://127.0.0.1:11434"

    EMBEDDING_PROVIDER: str = "chroma"  # "chroma" | "local" | "openai"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_API_KEY: str = ""

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)
