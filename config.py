"""Application configuration.

Temporary credentials live here until Supabase Auth replaces them.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Always load project .env (override empty values left by a previous process)
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH, override=True)


def _normalize_db_url(raw: str) -> str:
    """Convert Supabase-style URLs to a SQLAlchemy + psycopg2 URI."""
    url = (raw or "").strip().strip('"').strip("'")
    if not url:
        return ""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _build_db_url_from_parts() -> str:
    """Optional parts-based URL if SUPABASE_DB_URL is not set."""
    host = os.getenv("SUPABASE_DB_HOST", "").strip()
    password = os.getenv("SUPABASE_DB_PASSWORD", "")
    if not host or not password:
        return ""
    user = os.getenv("SUPABASE_DB_USER", "postgres").strip()
    port = os.getenv("SUPABASE_DB_PORT", "5432").strip()
    name = os.getenv("SUPABASE_DB_NAME", "postgres").strip()
    return (
        f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


class Config:
    """Base configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "packs-dev-secret-change-me")

    # Temporary login (replace with Supabase Auth later)
    TEMP_USERNAME = "admin"
    TEMP_PASSWORD = "admin123"

    # Fixed UUID for temporary admin until Supabase Auth (user_id column is uuid)
    DEFAULT_USER_ID = os.getenv(
        "DEFAULT_USER_ID",
        "00000000-0000-4000-8000-000000000001",
    )

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "").strip()

    _db_url = _normalize_db_url(SUPABASE_DB_URL) or _build_db_url_from_parts()
    DATABASE_CONFIGURED = bool(_db_url) and not _db_url.startswith("sqlite:")

    # Real DB when configured; otherwise a local placeholder so Flask can boot
    SQLALCHEMY_DATABASE_URI = _db_url or "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = (
        {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {"sslmode": "require"},
        }
        if DATABASE_CONFIGURED
        else {}
    )

    # Bunny.net Storage
    BUNNY_STORAGE_ZONE = os.getenv("BUNNY_STORAGE_ZONE", "")
    BUNNY_ACCESS_KEY = os.getenv("BUNNY_ACCESS_KEY", "")
    BUNNY_REGION = os.getenv("BUNNY_REGION", "")
    BUNNY_PULL_ZONE = os.getenv("BUNNY_PULL_ZONE", "")

    # Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
