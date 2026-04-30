import os
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


def build_database_uri():
    configured_uri = os.getenv("DATABASE_URL")
    if configured_uri:
        if configured_uri.startswith("postgres://"):
            return configured_uri.replace("postgres://", "postgresql://", 1)
        return configured_uri

    if os.getenv("VERCEL"):
        # Vercel functions expose writable scratch space via the system temp dir.
        temp_db = Path(tempfile.gettempdir()) / "taskcore.db"
        return f"sqlite:///{temp_db.as_posix()}"

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    local_db = INSTANCE_DIR / "database.db"
    return f"sqlite:///{local_db.as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
