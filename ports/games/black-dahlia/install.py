import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox import DosBoxWin9x
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE,
    FIRST_CD_DRIVE_LETTER,
)
from lib.dosbox.dosbox_win9x import DosBoxWin9xConf
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.utils import template

CURRENT_DIR = Path(__file__).resolve().parent
FILES_DIR = CURRENT_DIR / "files"

APP_DRIVE_SIZE = 100
APP_EXEC_PATH = APP_DIR / "BD_WIN.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE / "SETUP.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "8CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_DRIVE_LETTER)
            dbox = DosBoxWin9x(dst_folder, app_desc, DosBoxWin9xConf(app_drive_size=APP_DRIVE_SIZE))
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_DRIVE_LETTER, len(app_desc.distro.files)))
            dbox.run(INSTALLER_EXEC_PATH)
            dbox.copy(src_folder / "BDPATCH.EXE", APP_DIR)
            dbox.run(APP_DIR / "BDPATCH.EXE")
            # fixes CDs paths and enables subtitles in a patched version
            template(
                CURRENT_DIR / "templates" / "bd.ini.tmpl",
                APP_DIR / "BD.INI",
                params={"first_cd_letter": FIRST_CD_DRIVE_LETTER},
                newline="\r\n",
            )
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
