import json
import sys

from lib.app_desc import AppDesc
from lib.dosbox.const import (
    APP_DIR,
    FIRST_CD_DRIVE,
    FIRST_CD_DRIVE_LETTER,
)
from lib.dosbox.dosbox_conf import DosBoxMod
from lib.dosbox.dosbox_dos import (
    DosBoxDos,
    DosBoxDosConf,
)
from lib.dosbox.helpers import (
    copy_distro_files_as_cd_letters,
    gen_cd_mount_points,
)
from lib.errors import UnknownDistroFormatException
from lib.installer import Installer

APP_EXEC_PATH = APP_DIR / "TB.BAT"
INSTALLER_EXEC_PATH = FIRST_CD_DRIVE / "INSTDOS.EXE"


class Main(Installer):
    def __init__(self, app_desc: AppDesc):
        super().__init__(app_desc)
        dst_folder = app_desc.dst_path()
        src_folder = app_desc.src_path()
        if app_desc.distro.format == "1CD":
            copy_distro_files_as_cd_letters(src_folder, dst_folder, app_desc.distro.files, FIRST_CD_DRIVE_LETTER)
            dbox = DosBoxDos(dst_folder, app_desc, DosBoxDosConf(mod=DosBoxMod.X))
            dbox.mount(gen_cd_mount_points(dst_folder, FIRST_CD_DRIVE_LETTER, len(app_desc.distro.files)))
            dbox.run(INSTALLER_EXEC_PATH)
            dbox.run(APP_EXEC_PATH, mock=True)
        else:
            raise UnknownDistroFormatException(app_desc.distro)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    Main(AppDesc(**json.loads(sys.argv[1])))
