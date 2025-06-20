import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR"))
APPS_BUNDLE_DIR = DATA_DIR / "apps"
APPS_SRC_DIR = DATA_DIR / "apps_src"

APP_DIR_NAME = "APP"
# DEST_APP_DIR is defined dynamically in utils.enrich_vars()

FIRST_FD_DRIVE_LETTER = "A"
SECOND_FD_DRIVE_LETTER = "B"
FIRST_CD_DRIVE_LETTER = "E"
SECOND_CD_DRIVE_LETTER = "F"
THIRD_CD_DRIVE_LETTER = "G"
FOURTH_CD_DRIVE_LETTER = "H"
FIFTH_CD_DRIVE_LETTER = "I"
