import os
from pathlib import (
    Path,
    PureWindowsPath,
)

SYSTEM_DRIVE_LETTER = "C"
APP_DRIVE_LETTER = "D"
FIRST_CD_DRIVE_LETTER = "E"
SECOND_CD_DRIVE_LETTER = "F"
THIRD_CD_DRIVE_LETTER = "G"

SYSTEM_DRIVE = PureWindowsPath(f"{SYSTEM_DRIVE_LETTER}:")
APP_DRIVE = PureWindowsPath(f"{APP_DRIVE_LETTER}:")
APP_DIR = f"{APP_DRIVE}/APP"
FIRST_CD_DRIVE = PureWindowsPath(f"{FIRST_CD_DRIVE_LETTER}:")
SECOND_CD_DRIVE = PureWindowsPath(f"{SECOND_CD_DRIVE_LETTER}:")
THIRD_CD_DRIVE = PureWindowsPath(f"{THIRD_CD_DRIVE_LETTER}:")

# deprecated
# TODO: drop
FIRST_CD_LETTER = "E"
SECOND_CD_LETTER = "F"
THIRD_CD_LETTER = "G"
SYSTEM_DRIVE_DIR = PureWindowsPath(f"{SYSTEM_DRIVE_LETTER}:\\")
APP_DRIVE_DIR = PureWindowsPath(f"{APP_DRIVE_LETTER}:\\")
FIRST_CD_DRIVE_DIR = PureWindowsPath(f"{FIRST_CD_LETTER}:\\")
SECOND_CD_DRIVE_DIR = PureWindowsPath(f"{SECOND_CD_LETTER}:\\")
THIRD_CD_DRIVE_DIR = PureWindowsPath(f"{THIRD_CD_LETTER}:\\")
# end drop

RUNNERS_BASE_DIR = Path(os.environ["DATA_DIR"]) / "runners"  # TODO: move to the base runners' class
RUNNERS_BUNDLES_BASE_DIR = RUNNERS_BASE_DIR / "bundles"
RUNNERS_SRC_BASE_DIR = RUNNERS_BASE_DIR / "src"

CONF_NAME = "dosbox.conf"
