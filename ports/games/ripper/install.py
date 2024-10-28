import json
import sys
from pathlib import Path

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
    SYSTEM_DRIVE_LETTER,
)
from lib.dosbox.dosbox_dos import DosBoxDos
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.utils import (
    copy,
    template,
)

CURRENT_DIR = Path(__file__).resolve().parent

APP_EXEC_PATH = APP_DIR / "RIPPER.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "INSTALL.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        app_folder = dst_folder / APP_DRIVE_LETTER / "APP"
        src_folder = app_desc.src_path()

        if app_desc.distro.format == "6CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxDos(dst_folder, app_desc)
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            dbox.run(INSTALLER_EXEC_PATH)
            copy(app_desc.src_path() / "rip103.exe", app_folder)
            dbox.run(APP_DIR / "RIP103.EXE")
            copy(app_desc.src_path() / "rip105.exe", app_folder)
            dbox.run(APP_DIR / "RIP105.EXE")
            copy(CURRENT_DIR / "files" / "SETTINGS.DEF", app_folder)
            template(
                CURRENT_DIR / "templates" / "take2.ini.tmpl",
                dst_folder / SYSTEM_DRIVE_LETTER / "TAKE2.INI",
                params={"first_cd_letter": FIRST_CD_LETTER},
                newline="\r\n",
            )
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
