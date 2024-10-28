import json
import sys
from pathlib import (
    Path,
    PureWindowsPath,
)

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    APP_DRIVE_LETTER,
    FIRST_CD_DRIVE_DIR,
    FIRST_CD_LETTER,
)
from lib.dosbox.dosbox_dos import DosBoxDos
from lib.dosbox.helpers import gen_cd_mount_points
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer
from lib.unpack import unpack_disc_image
from lib.utils import (
    copy,
    rm,
)

CURRENT_DIR = Path(__file__).resolve().parent

APP_EXEC_PATH = APP_DIR / "picture"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE_DIR / "INSTALL.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        app_folder = dst_folder / APP_DRIVE_LETTER / "APP"
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            unpack_disc_image(src_folder / app_desc.distro.files[0], dst_folder / FIRST_CD_LETTER)
            dbox = DosBoxDos(dst_folder, app_desc)
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_LETTER, len(app_desc.distro.files)))
            dbox.run(INSTALLER_EXEC_PATH)
            pdi = "ENGLISH.PDI"
            if app_desc.lang == "es":
                pdi = "ESPA?OL.PDI"
            copy(dst_folder / FIRST_CD_LETTER / pdi / "WESTERN", app_folder)
            copy(CURRENT_DIR / "files" / "DIG.INI", app_folder)
            copy(CURRENT_DIR / "files" / "MDI.INI", app_folder)
            dbox.umount(FIRST_CD_LETTER)
            rm(dst_folder / FIRST_CD_LETTER)
            dbox.run(APP_EXEC_PATH, [PureWindowsPath(APP_DIR / "WESTERN")], mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
