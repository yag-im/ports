import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox import DosBoxWin9x
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_DIR,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SECOND_CD_DRIVE_DIR,
    SECOND_CD_LETTER,
    SYSTEM_DRIVE_DIR,
)
from lib.dosbox.dosbox_conf import DosBoxFlavor
from lib.dosbox.dosbox_win9x import DosBoxWin9xConf
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.utils import rm

CURRENT_DIR = Path(__file__).resolve().parent

APP_DRIVE_SIZE = 1000
APP_EXEC_PATH = APP_DIR / "rent-a-hero.exe"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "Setup" / "Setup.exe"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "2CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxWin9x(
                dst_folder, app_desc, DosBoxWin9xConf(flavor=DosBoxFlavor.WIN98SE, app_drive_size=APP_DRIVE_SIZE)
            )
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            dbox.copy(
                [
                    FIRST_CD_DRIVE_DIR / "Game" / "*",
                    SECOND_CD_DRIVE_DIR / "Game" / "*",
                ],
                APP_DRIVE_DIR / "Game",
            )
            dbox.run(INSTALLER_EXEC_PATH, runexit=False)
            dbox.copy(CURRENT_DIR / "files" / "RAH.INI", SYSTEM_DRIVE_DIR / "windows")
            dbox.umount(FIRST_CD_LETTER)
            dbox.umount(SECOND_CD_LETTER)
            rm(dst_folder / FIRST_CD_LETTER)
            rm(dst_folder / SECOND_CD_LETTER)
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
