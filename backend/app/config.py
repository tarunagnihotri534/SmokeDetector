import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS_DIR = BASE_DIR / "backend" / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'backend' / 'smoke_detector.db'}")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
