import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "ml" / "models"

# Detection Configuration Parameters (Preserved from spec)
PERSON_CONF: float = 0.40       # Person detection confidence threshold
CIG_CONF: float = 0.25          # Cigarette detection confidence threshold
IOU_THRESH: float = 0.45        # NMS IoU threshold
OVERLAP_THRESH: float = 0.30    # Containment ratio threshold (cig area inside person bbox)

# Debounce State Machine Configuration
DEBOUNCE_FRAMES: int = 5        # Required consecutive smoking frames before flipping to "violation"

# Model paths
PERSON_MODEL: str = os.environ.get("PERSON_MODEL", str(MODELS_DIR / "yolo11s.pt"))
CIGARETTE_MODEL: str = os.environ.get("CIGARETTE_MODEL", str(MODELS_DIR / "best.pt"))
