import json
import sys

from lib.app_desc import AppDesc
from lib.dosbox import DosBoxWin9x
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.dosbox.dosbox_conf import DosBoxFlavor
from lib.dosbox.dosbox_win9x import DosBoxWin9xConf
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer

APP_DRIVE_SIZE = 500
APP_EXEC_PATH = APP_DIR / "TITBIT.EXE"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "SETUP.EXE"

# Game requires modern OpenGL video card and crashes somewhere in OpenGL init block (0x41F35B)


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_LETTER)
            dbox = DosBoxWin9x(
                dst_folder,
                DosBoxWin9xConf(app_drive_size=APP_DRIVE_SIZE, flavor=DosBoxFlavor.WIN98SE, memsize=128),
            )
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            dbox.run("Explorer.exe", exit=False)
            # dbox.run(INSTALLER_EXEC_PATH)
            # dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
