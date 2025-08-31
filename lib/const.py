import os
from pathlib import Path

RUNNERS_BASE_DIR = Path(os.environ["DATA_DIR"]) / "runners"
RUNNERS_BUNDLES_BASE_DIR = RUNNERS_BASE_DIR / "bundles"

SYSTEM_DRIVE_LETTER = "C"
APP_DRIVE_LETTER = "D"
