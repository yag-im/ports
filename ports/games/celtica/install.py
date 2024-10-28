import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox import DosBoxWin9x
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SECOND_CD_DRIVE_DIR,
)
from lib.dosbox.dosbox_win9x import DosBoxWin9xConf
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
    unmount_remove_mounted_cds,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer

CURRENT_DIR = Path(__file__).resolve().parent

APP_DRIVE_SIZE = 1000
APP_EXEC_PATH = APP_DIR / "CELTICA.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "setup.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "2CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxWin9x(dst_folder, app_desc, DosBoxWin9xConf(app_drive_size=APP_DRIVE_SIZE))
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            dbox.copy(
                [
                    FIRST_CD_DRIVE_DIR / "Celtica" / "*",
                    SECOND_CD_DRIVE_DIR / "Celtica" / "*",
                ],
                APP_DRIVE_DIR / "Celtica",
            )
            dbox.run(INSTALLER_EXEC_PATH)
            dbox.regedit(
                {
                    "HKEY_LOCAL_MACHINE\\SOFTWARE\\H+a\\Celtica": [
                        {"CD Location": f"{APP_DRIVE_LETTER}:"},
                        {"Dir": APP_DIR},
                    ]
                }
            )
            unmount_remove_mounted_cds(dbox, dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files))
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
